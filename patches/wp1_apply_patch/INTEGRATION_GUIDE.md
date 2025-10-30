# ИНСТРУКЦИЯ ПО ИНТЕГРАЦИИ /agent/apply_patch
# WP-1 из SPEC_STAGE1_COMPLETION.md

## ШАГИ ИНТЕГРАЦИИ:

1. КОПИРОВАНИЕ ФАЙЛОВ:
   - Скопировать apply_patch_router.py в /app/apply_patch_router.py в контейнере crd12_engineer_b_api

2. ИМПОРТ В MAIN.PY:
   - Добавить в /app/main.py:
     from apply_patch_router import router as apply_patch_router
   
   - Добавить регистрацию роутера:
     app.include_router(apply_patch_router, prefix="/api/v1", tags=["patches"])

3. ОБНОВЛЕНИЕ ЗАВИСИМОСТЕЙ:
   - Добавить в requirements.txt:
     requests>=2.25.0

4. ПЕРЕЗАПУСК СЕРВИСА:
   - Выполнить в контейнере:
     supervisorctl restart uvicorn

## ПРОВЕРКА РАБОТОСПОСОБНОСТИ:

1. ТЕСТ ЭНДПОИНТА:
   POST http://localhost:8030/api/v1/agent/apply_patch
   Content-Type: application/json
   
   {
     "target_filepath": "/app/src/marker_selfbuild.py",
     "code": "def marker_selfbuild():\\n    return \\\"STAGE1_WP1_APPLY_PATCH_WORKS\\\"\\n",
     "job_id": "test_wp1_001"
   }

2. ПРОВЕРКА СОБЫТИЙ:
   GET http://localhost:8031/events?limit=5

3. ПРОВЕРКА ПАТЧЕЙ:
   GET http://localhost:8030/api/v1/agent/patches

## ОЖИДАЕМЫЙ РЕЗУЛЬТАТ:
- Событие PATCH_APPLIED в core.events
- Файл обновлен с созданием бэкапа
- Возврат статуса "applied" с hash и backup путем
