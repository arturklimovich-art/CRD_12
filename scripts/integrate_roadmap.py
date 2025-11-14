import os
import re
from datetime import datetime

APP_PATH = r"C:\Users\Artur\Documents\CRD12\src\app\engineer_b_api\app.py"
BACKUP_DIR = r"C:\Users\Artur\Documents\CRD12\backups\app_py"

os.makedirs(BACKUP_DIR, exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = os.path.join(BACKUP_DIR, f"app.py.backup_{timestamp}")

with open(APP_PATH, 'r', encoding='utf-8') as f:
    content = f.read()

with open(backup_path, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"✅ Backup: {backup_path}")

roadmap_import = '''
# === ROADMAP MODULE INTEGRATION ===
try:
    from routes.roadmap import router as roadmap_router
    ROADMAP_AVAILABLE = True
except Exception as e_roadmap:
    print(f"WARNING: Roadmap module not available: {e_roadmap}")
    ROADMAP_AVAILABLE = False

'''

pattern = r'(import importlib\n)'
match = re.search(pattern, content)
if match:
    insert_pos = match.end()
    content = content[:insert_pos] + roadmap_import + content[insert_pos:]
    print("✅ Step 1: Roadmap import added")
else:
    print("❌ ERROR: Could not find 'import importlib'")
    exit(1)

content = content.replace('version="4.0 - Self-Healing"', 'version="4.1 - Self-Healing + Roadmap"')
print("✅ Step 2: Version updated to 4.1")

router_reg = '''
# Register Roadmap router
if ROADMAP_AVAILABLE:
    app.include_router(roadmap_router)
    print("✅ Roadmap router registered")

'''

pattern = r'(app = FastAPI\(title="Engineer B API", version="4\.1 - Self-Healing \+ Roadmap"\)\n)'
match = re.search(pattern, content)
if match:
    insert_pos = match.end()
    content = content[:insert_pos] + router_reg + content[insert_pos:]
    print("✅ Step 3: Router registration added")
else:
    print("❌ ERROR: Could not find FastAPI app declaration")
    exit(1)

with open(APP_PATH, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"\n🎉 SUCCESS: app.py patched successfully!")
print(f"📁 Backup location: {backup_path}")
