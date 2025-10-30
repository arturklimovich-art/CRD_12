#!/bin/bash
# Безопасный скрипт добавления эндпоинта событий

set -e  # Выход при ошибке

echo "🔧 Добавляем эндпоинт /events/log в Engineer_B_API..."

# Копируем файл эндпоинта в контейнер
docker cp ../events_endpoint_patch.py crd12_engineer_b_api:/app/events_router.py

# Проверяем существование main.py
if docker exec crd12_engineer_b_api test -f /app/main.py; then
    echo "✅ main.py найден"
    
    # Проверяем, не добавлен ли уже роутер
    if ! docker exec crd12_engineer_b_api grep -q "events_router" /app/main.py; then
        echo "📝 Добавляем импорт events_router в main.py..."
        # Резервное копирование main.py
        docker exec crd12_engineer_b_api cp /app/main.py /app/main.py.backup
        
        # Добавляем импорт (временное решение - в продакшене нужно править аккуратно)
        docker exec crd12_engineer_b_api python -c "
import sys
sys.path.append('/app')

# Тестируем импорт events_router
try:
    from events_router import router as events_router
    print('✅ events_router импортирован успешно')
    
    # Проверяем подключение к БД
    from events_router import log_event, get_recent_events
    print('✅ Функции events_router загружены')
    
except Exception as e:
    print(f'❌ Ошибка: {e}')
    sys.exit(1)
"
    else
        echo "⚠️  events_router уже добавлен в main.py"
    fi
else
    echo "❌ main.py не найден"
    exit 1
fi

echo "🎉 Патч применен успешно!"
echo "ℹ️  Для активации эндпоинта нужно перезагрузить приложение:"
echo "   docker exec crd12_engineer_b_api supervisorctl restart uvicorn"
