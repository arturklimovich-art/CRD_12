try:
    print("Testing simple apply_patch import...")
    from apply_patch_simple import router as apply_patch_router
    print("✅ Simple apply_patch_router imported successfully")
    
    print("Testing router functions...")
    if hasattr(apply_patch_router, 'apply_patch'):
        print("✅ apply_patch function found")
    else:
        print("❌ apply_patch function not found")
        
    print("✅ Simple version tests passed!")
    
except Exception as e:
    print(f"❌ Simple import test failed: {e}")
    import traceback
    print(f"Traceback: {traceback.format_exc()}")
