from typing import Dict, Any, Tuple, Optional
from loguru import logger
import importlib.util
from pathlib import Path

class PatchService:
    def __init__(self, patch_manager=None):
        self.patch_manager = patch_manager
        if patch_manager is None:
            try:
                from patch_manager import PatchManager
                import os
                db_dsn = os.getenv("DATABASE_URL", "postgresql://crd_user:crd12@crd12_pgvector:5432/crd12")
                self.patch_manager = PatchManager(db_dsn=db_dsn)
            except ImportError:
                logger.warning("PatchManager not available, will use direct apply method")
                self.patch_manager = None

    async def apply_patch(self, target_file: str, generated_code: str, task_id: str, review_result: Dict[str, Any]) -> Tuple[bool, str, Optional[str]]:
        """
        Единый метод для применения патчей через централизованный PatchManager
        """
        if not review_result.get("approved", False):
            reason = review_result.get("reason", "Code not approved by curator")
            logger.warning(f"Refusing to apply patch: {reason}")
            return False, f"Patch rejected: {reason}", None

        if self.patch_manager is None:
            return self._apply_directly(target_file, generated_code)
        
        try:
            patch_id, approve_token = self.patch_manager.create_patch_from_generated_code(
                target_file=target_file,
                generated_code=generated_code,
                task_id=task_id,
                author="patch_service_auto"
            )
            
            success, message = self.patch_manager.apply_patch_with_token(
                patch_id=patch_id,
                approve_token=approve_token,
                target_file=target_file
            )
            
            if success:
                logger.info(f"Patch {patch_id} applied successfully to {target_file}")
                return True, f"Patch {patch_id} applied successfully", patch_id
            else:
                logger.error(f"Failed to apply patch {patch_id}: {message}")
                return False, f"Failed to apply patch: {message}", patch_id
                
        except Exception as e:
            logger.exception(f"Error applying patch through PatchManager: {e}")
            return False, f"Error applying patch: {str(e)}", None

    def _apply_directly(self, filepath: str, code: str) -> Tuple[bool, str, Optional[str]]:
        """
        Резервный метод прямого применения кода (для совместимости)
        """
        try:
            compiled_code = compile(code, filepath, 'exec')
            
            backup_path = f"{filepath}.backup_{int(__import__('time').time())}"
            if Path(filepath).exists():
                Path(filepath).replace(backup_path)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(code)
            
            spec = importlib.util.spec_from_file_location("__temp__", filepath)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            logger.info(f"Direct code application successful: {filepath}")
            return True, f"Direct application successful, backup at {backup_path}", backup_path
            
        except SyntaxError as e:
            error_msg = f"Syntax error in code: {str(e)}"
            logger.error(error_msg)
            return False, error_msg, None
        except Exception as e:
            error_msg = f"Failed to apply code directly: {str(e)}"
            logger.exception(error_msg)
            return False, error_msg, None