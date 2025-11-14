import sys
sys.path.insert(0, '/app')
from patch_manager import PatchManager
import os

DB_DSN = os.getenv("DATABASE_URL", "postgres://crd_user:crd12@crd12_pgvector:5432/crd12")

print("?? FINAL TEST: PatchManager v1.2")
print("=" * 60)

test_code = """
def final_test_function():
    return "PatchManager v1.2 works!"
"""

try:
    pm = PatchManager(db_dsn=DB_DSN)
    patch_id, token = pm.create_patch_from_generated_code(
        target_file="agents/final_test.py",
        generated_code=test_code,
        task_id="test_task_pm_final",
        author="final_test"
    )
    print(f"? SUCCESS!")
    print(f"   Patch ID: {patch_id}")
    print(f"   Token: {token}")
except Exception as e:
    print(f"? FAILED: {e}")
    sys.exit(1)
