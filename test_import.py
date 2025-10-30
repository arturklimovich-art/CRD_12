try:
    from jobs_ultra_simple import router
    print("✅ Импорт успешен")
    print("✅ Router создан:", router is not None)
except Exception as e:
    print(f"❌ Ошибка импорта: {e}")
    import traceback
    traceback.print_exc()
