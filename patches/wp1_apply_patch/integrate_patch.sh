#!/bin/bash
# Скрипт автоматической интеграции /agent/apply_patch
# Engineers_IT Core - WP-1 Implementation

set -e

echo "🔧 Integrating /agent/apply_patch endpoint..."

# Копируем роутер в контейнер
docker cp apply_patch_router.py crd12_engineer_b_api:/app/apply_patch_router.py

# Проверяем существование main.py
if docker exec crd12_engineer_b_api test -f /app/main.py; then
    echo "✅ main.py found"
    
    # Проверяем, не добавлен ли уже роутер
    if ! docker exec crd12_engineer_b_api grep -q "apply_patch_router" /app/main.py; then
        echo "📝 Adding apply_patch_router to main.py..."
        
        # Создаем backup main.py
        docker exec crd12_engineer_b_api cp /app/main.py /app/main.py.backup_wp1
        
        # Создаем временный файл с импортом
        docker exec crd12_engineer_b_api python -c "
# Тестируем импорт нового роутера
try:
    from apply_patch_router import router as apply_patch_router
    print('✅ apply_patch_router imported successfully')
    
    # Тестируем зависимости
    import requests
    print('✅ requests module available')
    
    print('✅ All dependencies satisfied')
    
except Exception as e:
    print(f'❌ Import failed: {e}')
    exit(1)
"
    else
        echo "⚠️ apply_patch_router already exists in main.py"
    fi
else
    echo "❌ main.py not found"
    exit 1
fi

# Добавляем requests в requirements.txt если нужно
if ! docker exec crd12_engineer_b_api grep -q "requests" /app/requirements.txt 2>/dev/null; then
    echo "📦 Adding requests to requirements.txt..."
    docker exec crd12_engineer_b_api sh -c "echo 'requests>=2.25.0' >> /app/requirements.txt"
    docker exec crd12_engineer_b_api pip install requests
fi

echo "🎉 Integration preparation completed!"
echo "ℹ️  Manual steps required:"
echo "   1. Add import to main.py: from apply_patch_router import router as apply_patch_router"
echo "   2. Add router registration: app.include_router(apply_patch_router, prefix=\"/api/v1\", tags=[\"patches\"])"
echo "   3. Restart service: docker exec crd12_engineer_b_api supervisorctl restart uvicorn"
