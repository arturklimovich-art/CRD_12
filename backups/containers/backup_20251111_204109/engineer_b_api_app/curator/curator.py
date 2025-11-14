# -*- coding: utf-8 -*-
"""
Curator v1.0 — SAST + micro-DAST gate for self-deploy patches.
Совместим с app.py (S1-FIX-SELF-DEPLOY). Без внешних зависимостей.
"""
from __future__ import annotations
import ast, os, re, json, hashlib, tempfile, subprocess, sys, textwrap
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

APP_ROOT = "/app"

@dataclass
class CuratorPolicy:
    allow_paths_prefix: List[str] = (APP_ROOT,)
    max_lines: int = 2000
    max_bytes: int = 300_000
    max_func_complexity: int = 25
    allow_httpx: bool = True
    banned_imports: List[str] = (
        "subprocess","shutil","socket","ftplib","telnetlib","paramiko","asyncssh","fabric",
        "multiprocessing","pickle"
    )
    soft_imports: List[str] = ("os","sys","pathlib")
    banned_calls: List[str] = ("eval","exec","compile","os.system","subprocess.Popen",
                               "subprocess.run","subprocess.check_call","subprocess.check_output",
                               "shutil.rmtree","open")
    secret_patterns: List[str] = (
        r"(?i)(api[_-]?key|secret|token|password)\s*[:=]\s*['\"][A-Za-z0-9_\-]{16,}['\"]",
        r"(?i)sk-[A-Za-z0-9]{20,}",
    )
    micro_dast_timeout_sec: int = 5

def _load_policy_from_env() -> CuratorPolicy:
    raw = os.getenv("CURATOR_POLICY_JSON")
    if not raw:
        return CuratorPolicy()
    try:
        data = json.loads(raw)
        base = CuratorPolicy()
        for k,v in data.items():
            setattr(base, k, v)
        return base
    except Exception:
        return CuratorPolicy()

def _under_app_root(path: str) -> bool:
    try:
        if not path: return False
        rp = os.path.realpath(path)
        rr = os.path.realpath(APP_ROOT)
        return rp == rr or rp.startswith(rr + os.sep)
    except Exception:
        return False

def _estimate_cyclomatic_complexity(tree: ast.AST) -> int:
    nodes = (ast.If, ast.For, ast.AsyncFor, ast.While, ast.With, ast.Try, ast.BoolOp,
             ast.IfExp, ast.And, ast.Or, ast.ExceptHandler, ast.comprehension)
    count = 1
    for n in ast.walk(tree):
        if isinstance(n, nodes):
            count += 1
    return count

def _find_calls(tree: ast.AST) -> List[str]:
    calls = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Call):
            name_parts = []
            curr = n.func
            while isinstance(curr, (ast.Attribute, ast.Name)):
                if isinstance(curr, ast.Attribute):
                    name_parts.append(curr.attr); curr = curr.value
                elif isinstance(curr, ast.Name):
                    name_parts.append(curr.id); break
            full = ".".join(reversed(name_parts)) if name_parts else ""
            if full:
                calls.append(full)
    return calls

def _find_imports(tree: ast.AST) -> List[str]:
    imps = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            for a in n.names:
                imps.append(a.name.split(".")[0])
        elif isinstance(n, ast.ImportFrom):
            if n.module:
                imps.append(n.module.split(".")[0])
    return imps

def _contains_secrets(code: str, patterns: List[str]) -> Optional[str]:
    for pat in patterns:
        if re.search(pat, code):
            return pat
    return None

class Curator:
    def __init__(self, put_event=None, upload_artifact=None):
        self.policy = _load_policy_from_env()
        self.put_event = put_event or (lambda **k: None)
        self.upload_artifact = upload_artifact or (lambda *a, **k: None)

    def review(self,
               task_text: str,
               code: str,
               target_path: Optional[str],
               job_id: Optional[str] = None,
               idempotency_key: Optional[str] = None) -> Dict[str, Any]:
        reasons: List[str] = []
        metrics: Dict[str, Any] = {}
        decision = "reject"

        code_norm = textwrap.dedent(code or "").lstrip("\ufeff")
        lines = code_norm.count("\n") + 1
        size = len(code_norm.encode("utf-8", "replace"))
        metrics.update({"lines": lines, "bytes": size})
        if not code_norm.strip():
            reasons.append("Пустой код.")
            return self._result(decision, reasons, 0, metrics)

        if lines > self.policy.max_lines: reasons.append(f"Слишком много строк: {lines}>{self.policy.max_lines}")
        if size  > self.policy.max_bytes: reasons.append(f"Слишком большой размер: {size}>{self.policy.max_bytes}")

        if target_path:
            if not _under_app_root(target_path):
                reasons.append(f"Целевой путь вне {APP_ROOT}: {target_path}")
        else:
            reasons.append("Не определён целевой путь (target_path).")

        try:
            tree = ast.parse(code_norm, filename=target_path or "<patch>", mode="exec")
        except SyntaxError as e:
            reasons.append(f"Синтаксическая ошибка: {e}")
            return self._result(decision, reasons, 0, metrics)

        imports = _find_imports(tree)
        calls   = _find_calls(tree)
        metrics.update({"imports": imports, "calls": calls})

        for mod in self.policy.banned_imports:
            if mod in imports:
                reasons.append(f"Запрещённый import: {mod}")

        if not self.policy.allow_httpx and "httpx" in imports:
            reasons.append("Запрещённый import: httpx (policy.allow_httpx=false)")

        for bc in self.policy.banned_calls:
            if bc in calls:
                reasons.append(f"Запрещённый вызов: {bc}")

        pat = _contains_secrets(code_norm, self.policy.secret_patterns)
        if pat:
            reasons.append("Похоже на секрет/ключ в коде (pattern match).")

        if "open" in calls and "open" in self.policy.banned_calls:
            for n in ast.walk(tree):
                if isinstance(n, ast.Call):
                    name = []
                    curr = n.func
                    while isinstance(curr, (ast.Attribute, ast.Name)):
                        if isinstance(curr, ast.Attribute):
                            name.append(curr.attr); curr = curr.value
                        else:
                            name.append(curr.id); break
                    full = ".".join(reversed(name)) if name else ""
                    if full == "open" and n.args:
                        arg0 = n.args[0]
                        if isinstance(arg0, ast.Constant) and isinstance(arg0.value, str):
                            if not _under_app_root(arg0.value):
                                reasons.append(f"open() вне {APP_ROOT}: {arg0.value}")
                        else:
                            reasons.append("open() с недетерминированным путём.")

        complexity = _estimate_cyclomatic_complexity(tree)
        metrics["complexity"] = complexity
        if complexity > self.policy.max_func_complexity:
            reasons.append(f"Сложность кода слишком высока: {complexity}>{self.policy.max_func_complexity}")

        critical_flags = any(s for s in reasons if any(k in s.lower() for k in [
            "запрещ", "секрет", "вне /app", "синтакс", "слишком большой", "не определён целевой путь"
        ]))
        if not critical_flags:
            ok, msg = self._micro_dast_import_check(code_norm, job_id)
            metrics["micro_dast"] = msg
            if not ok:
                reasons.append(f"Микро-DAST не пройдён: {msg}")

        score = 100
        if reasons:
            score = max(0, 100 - 10*len(reasons))

        decision = "approve" if not reasons else "reject"
        return self._result(decision, reasons, score, metrics)

    def _micro_dast_import_check(self, code_norm: str, job_id: Optional[str]) -> Tuple[bool, str]:
        with tempfile.TemporaryDirectory() as td:
            p = os.path.join(td, "snippet.py")
            with open(p, "w", encoding="utf-8") as f:
                f.write(code_norm)
            env = os.environ.copy()
            env["PYTHONPATH"] = APP_ROOT
            env["NO_NET"] = "1"
            cmd = [sys.executable, "-c", f"import py_compile; py_compile.compile(r'{p}', doraise=True); import importlib.util; importlib.util.spec_from_file_location('snippet', r'{p}')"]
            try:
                r = subprocess.run(cmd, capture_output=True, text=True, timeout=_load_policy_from_env().micro_dast_timeout_sec, env=env)
                if r.returncode != 0:
                    return False, f"py_compile/spec failed: {r.stderr.strip()[:200]}"
                return True, "ok"
            except subprocess.TimeoutExpired:
                return False, "timeout"
            except Exception as e:
                return False, f"error: {type(e).__name__}: {e}"

    def _result(self, decision: str, reasons: List[str], score: int, metrics: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "decision": decision,
            "reasons": reasons,
            "score": score,
            "metrics": metrics,
        }