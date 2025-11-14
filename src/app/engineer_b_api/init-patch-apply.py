# /app/init-patch-apply.py (обновленная версия для E1-PATCH-MANUAL Integration)
import os
import uuid
import hashlib
import zipfile
import tempfile
from pathlib import Path
import psycopg2
import sys

def get_db_connection():
    """Подключение к БД"""
    try:
        return psycopg2.connect(
            host="localhost",
            port=5433,
            database="crd12",
            user="crd_user",
            password="crd12"
        )
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

def scan_and_register_patches():
    """Сканирует patches_applied и регистрирует патчи в БД"""
    patches_dir = Path("/app/workspace/patches_applied/")
    
    if not patches_dir.exists():
        print("ℹ️  No patches_applied directory found")
        return
    
    patch_files = list(patches_dir.glob("*.zip"))
    print(f"🔍 Found {len(patch_files)} patch files in {patches_dir}")
    
    for patch_file in patch_files:
        try:
            # Вычисляем хеш
            with open(patch_file, 'rb') as f:
                content = f.read()
                sha256 = hashlib.sha256(content).hexdigest()
            
            # Проверяем, не зарегистрирован ли уже патч
            conn = get_db_connection()
            if not conn:
                print("❌ Cannot connect to database, skipping patch registration")
                continue
                
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT id, filename, status FROM eng_it.patches WHERE sha256 = %s",
                    (sha256,)
                )
                existing = cursor.fetchone()
                
                if existing:
                    print(f"ℹ️  Patch {patch_file.name} already registered (ID: {existing[0]}, Status: {existing[2]})")
                    continue
            
            # Регистрируем новый патч
            register_patch_in_db(patch_file, content, sha256)
            print(f"✅ Registered patch: {patch_file.name}")
            
            conn.close()
            
        except Exception as e:
            print(f"❌ Failed to register patch {patch_file.name}: {str(e)}")

def register_patch_in_db(patch_file, content, sha256):
    """Регистрирует патч в базе данных"""
    conn = get_db_connection()
    if not conn:
        return
        
    try:
        with conn.cursor() as cursor:
            patch_id = str(uuid.uuid4())
            meta = {
                "size": len(content),
                "source": "auto_registered",
                "original_path": str(patch_file),
                "auto_detected": True
            }
            
            cursor.execute("""
                INSERT INTO eng_it.patches 
                (id, author, filename, content, sha256, status, meta)
                VALUES (%s, %s, %s, %s, %s, 'submitted', %s)
            """, (patch_id, "system", patch_file.name, content, sha256, meta))
            
            cursor.execute("""
                INSERT INTO eng_it.patch_events (patch_id, event_type, payload)
                VALUES (%s, 'patch.auto_registered', %s)
            """, (patch_id, {
                "filename": patch_file.name,
                "source": "init_script",
                "note": "Automatically registered during container startup"
            }))
            
            conn.commit()
            print(f"📝 Patch {patch_id} registered in database")
            
    except Exception as e:
        print(f"❌ Database error: {e}")
        conn.rollback()
    finally:
        conn.close()

def check_pending_patches():
    """Проверяет статусы патчей в БД"""
    conn = get_db_connection()
    if not conn:
        return
        
    try:
        with conn.cursor() as cursor:
            # Статистика по статусам
            cursor.execute("""
                SELECT status, COUNT(*) 
                FROM eng_it.patches 
                GROUP BY status 
                ORDER BY status
            """)
            stats = cursor.fetchall()
            
            if stats:
                print("📊 Current patches status:")
                for status, count in stats:
                    print(f"  {status}: {count} patches")
            else:
                print("ℹ️  No patches found in database")
                
    except Exception as e:
        print(f"❌ Error checking patches: {e}")
    finally:
        conn.close()

def main():
    print("=" * 50)
    print("🔄 E1-PATCH-MANUAL Integration Initialization")
    print("=" * 50)
    
    # 1. Сканируем и регистрируем существующие патчи
    print("📂 Step 1: Scanning for unregistered patches...")
    scan_and_register_patches()
    
    # 2. Показываем текущее состояние
    print("")
    print("📊 Step 2: Checking current patches status...")
    check_pending_patches()
    
    # 3. Информация о следующем шаге
    print("")
    print("💡 Next steps:")
    print("  - Patches are now registered in eng_it.patches table")
    print("  - Use Curator to validate and approve patches")
    print("  - Use Engineer_B to apply approved patches")
    print("  - Monitor progress via /api/patches endpoints")
    
    print("")
    print("✅ Patch initialization completed")

if __name__ == "__main__":
    main()
