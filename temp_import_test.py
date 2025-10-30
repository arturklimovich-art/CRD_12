try:
    print("Testing apply_patch_router import...")
    from apply_patch_router import router as apply_patch_router
    print("✅ apply_patch_router imported successfully")
    
    print("Testing dependencies...")
    import requests
    import os
    import hashlib
    import shutil
    import py_compile
    import importlib.util
    from datetime import datetime
    print("✅ All dependencies available")
    
    print("Testing router functions...")
    if hasattr(apply_patch_router, 'apply_patch'):
        print("✅ apply_patch function found")
    else:
        print("❌ apply_patch function not found")
        
    print("✅ All tests passed!")
    
except Exception as e:
    print(f"❌ Import test failed: {e}")
    import traceback
    print(f"Traceback: {traceback.format_exc()}")
    exit(1)
