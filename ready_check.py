#!/usr/bin/env python3
import subprocess
import requests
import time
import sys
import os

def run_cmd(cmd):
    """Выполнить команду и вернуть результат"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return -1, "", str(e)

def check_processes():
    """Проверить запущенные процессы"""
    print("=== Процессы ===")
    code, out, err = run_cmd("ps -ef | grep -E '(uvicorn|gunicorn|python|supervisor)'")
    print(out)
    return "uvicorn" in out or "gunicorn" in out

def check_ports():
    """Проверить слушающие порты"""
    print("\n=== Порт 8000 ===")
    code, out, err = run_cmd("netstat -tulpn | grep :8000 || ss -tulpn | grep :8000")
    print(out if out else "Порт 8000 не слушается")
    
    print("\n=== Порт 8030 (Supervisor) ===")
    code, out, err = run_cmd("netstat -tulpn | grep :8030 || ss -tulpn | grep :8030")
    print(out if out else "Порт 8030 не слушается")

def check_supervisor_health():
    """Проверить здоровье Supervisor"""
    print("\n=== Supervisor Health (8030) ===")
    try:
        resp = requests.get("http://127.0.0.1:8030/health", timeout=5)
        print(f"Status: {resp.status_code}")
        print(f"Response: {resp.text}")
        return resp.status_code == 200
    except Exception as e:
        print(f"Ошибка: {e}")
        return False

def check_worker_health():
    """Проверить здоровье воркера"""
    print("\n=== Worker Health (8000) ===")
    try:
        resp = requests.get("http://127.0.0.1:8000/ready", timeout=5)
        print(f"Status: {resp.status_code}")
        print(f"Response: {resp.text}")
        return resp.status_code == 200
    except Exception as e:
        print(f"Ошибка: {e}")
        return False

def check_supervisor_logs():
    """Показать логи Supervisor"""
    print("\n=== Логи Supervisor (последние 20 строк) ===")
    code, out, err = run_cmd("tail -20 /app/supervisor.log 2>/dev/null || echo 'Лог не найден'")
    print(out)

def check_worker_logs():
    """Показать логи воркера"""
    print("\n=== Логи Worker (последние 20 строк) ===")
    code, out, err = run_cmd("tail -20 /app/worker.log 2>/dev/null || echo 'Лог не найден'")
    print(out)

def main():
    print("🔍 Диагностика Engineer B API\n")
    
    processes_ok = check_processes()
    check_ports()
    supervisor_ok = check_supervisor_health()
    worker_ok = check_worker_health()
    
    if not worker_ok:
        print("\n⚠️ Воркер не отвечает, проверяем логи...")
        check_supervisor_logs()
        check_worker_logs()
    
    print(f"\n📊 Итог:")
    print(f"Процессы: {'✅' if processes_ok else '❌'}")
    print(f"Supervisor: {'✅' if supervisor_ok else '❌'}")
    print(f"Worker: {'✅' if worker_ok else '❌'}")

if __name__ == "__main__":
    main()
