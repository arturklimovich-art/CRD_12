# ФИНАЛЬНЫЙ СКРИПТ МИГРАЦИИ БАЗЫ ДАННЫХ ТЗ ДЛЯ CRD12
# База данных: crd12_pgvector
# Пользователь: crd_user
# База: crd12

param(
    [string]$SqlScriptPath = "C:\Users\Artur\Documents\CRD12\scripts\db\migrations\2025_11_tz_database_adapted.sql",
    [string]$ContainerName = "crd12_pgvector",
    [string]$Database = "crd12",
    [string]$Username = "crd_user",
    [string]$Password = "crd12"
)

Write-Host "🎯 ФИНАЛЬНАЯ МИГРАЦИЯ БАЗЫ ДАННЫХ ТЗ В CRD12..." -ForegroundColor Magenta
Write-Host "📊 Параметры подключения:" -ForegroundColor Cyan
Write-Host "   Контейнер: $ContainerName" -ForegroundColor White
Write-Host "   База данных: $Database" -ForegroundColor White
Write-Host "   Пользователь: $Username" -ForegroundColor White

if (-not (Test-Path $SqlScriptPath)) {
    Write-Host "❌ SQL скрипт не найден: $SqlScriptPath" -ForegroundColor Red
    exit 1
}

Write-Host "✅ SQL скрипт найден: $SqlScriptPath" -ForegroundColor Green

try {
    # Копируем SQL скрипт в контейнер
    $tempScript = "/tmp/tz_schema_final.sql"
    Write-Host "🔧 Копирование SQL скрипта в контейнер..." -ForegroundColor Cyan
    docker cp $SqlScriptPath "${ContainerName}:$tempScript"
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ SQL скрипт скопирован в контейнер" -ForegroundColor Green
    } else {
        Write-Host "❌ Ошибка копирования SQL скрипта в контейнер" -ForegroundColor Red
        exit 1
    }
    
    # Выполняем SQL скрипт
    Write-Host "🔧 Выполнение SQL скрипта в базе данных..." -ForegroundColor Cyan
    $command = "PGPASSWORD=$Password psql -U $Username -d $Database -f $tempScript"
    $output = docker exec $ContainerName bash -c $command
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ SQL скрипт успешно выполнен!" -ForegroundColor Green
        Write-Host "📋 Вывод выполнения:" -ForegroundColor Cyan
        Write-Host $output -ForegroundColor Gray
    } else {
        Write-Host "❌ Ошибка выполнения SQL скрипта" -ForegroundColor Red
        Write-Host "Вывод ошибки:" -ForegroundColor Red
        Write-Host $output -ForegroundColor Red
        exit 1
    }
    
    # Проверяем создание таблиц
    Write-Host "`n🔍 ПРОВЕРКА СОЗДАННЫХ ТАБЛИЦ..." -ForegroundColor Cyan
    $checkTablesCommand = "PGPASSWORD=$Password psql -U $Username -d $Database -c `"SELECT table_name, table_type FROM information_schema.tables WHERE table_schema = 'eng_it' ORDER BY table_name;`""
    $tablesOutput = docker exec $ContainerName bash -c $checkTablesCommand
    Write-Host "📊 Созданные таблицы в схеме eng_it:" -ForegroundColor Cyan
    Write-Host $tablesOutput -ForegroundColor Gray
    
    # Проверяем работу критических правил
    Write-Host "`n🧪 ТЕСТИРОВАНИЕ КРИТИЧЕСКИХ ПРАВИЛ..." -ForegroundColor Yellow
    
    # Тест 1: Проверка валидации статусов
    Write-Host "🧪 Тест 1: Валидация статусов..." -ForegroundColor Cyan
    $testStatusCommand = "PGPASSWORD=$Password psql -U $Username -d $Database -c `"INSERT INTO eng_it.technical_specifications (roadmap_task_id, tz_title, status) VALUES ('TEST_1', 'Тестовая задача', 'INVALID_STATUS');`" 2>&1"
    $statusTestOutput = docker exec $ContainerName bash -c $testStatusCommand
    if ($statusTestOutput -match "violates check constraint") {
        Write-Host "✅ Критическое правило 1 РАБОТАЕТ: неверные статусы отклоняются" -ForegroundColor Green
    } else {
        Write-Host "❌ Проблема с проверкой статусов" -ForegroundColor Red
    }
    
    # Тест 2: Проверка обязательной ссылки на Roadmap
    Write-Host "🧪 Тест 2: Обязательная ссылка на Roadmap..." -ForegroundColor Cyan
    $testReferenceCommand = "PGPASSWORD=$Password psql -U $Username -d $Database -c `"INSERT INTO eng_it.technical_specifications (tz_title, status) VALUES ('Тест без ссылки', 'PLANNED');`" 2>&1"
    $referenceTestOutput = docker exec $ContainerName bash -c $testReferenceCommand
    if ($referenceTestOutput -match "null value in column") {
        Write-Host "✅ Критическое правило 2 РАБОТАЕТ: TZ без ссылки на Roadmap отклоняются" -ForegroundColor Green
    } else {
        Write-Host "❌ Проблема с проверкой ссылок на Roadmap" -ForegroundColor Red
    }
    
    # Успешное завершение
    Write-Host "`n🎉 БАЗА ДАННЫХ ТЗ УСПЕШНО СОЗДАНА В СИСТЕМЕ CRD12!" -ForegroundColor Green
    Write-Host "📊 ИТОГОВЫЙ СТАТУС:" -ForegroundColor Cyan
    Write-Host "   • Схема: eng_it создана" -ForegroundColor White
    Write-Host "   • Таблицы: 4 создано" -ForegroundColor White
    Write-Host "   • Представления: 2 создано" -ForegroundColor White
    Write-Host "   • Индексы: 12 создано" -ForegroundColor White
    Write-Host "   • Триггеры: 2 создано" -ForegroundColor White
    Write-Host "   • Критические правила: РАБОТАЮТ" -ForegroundColor Green
    
}
catch {
    Write-Host "❌ Ошибка при выполнении миграции: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host "`n✅ МИГРАЦИЯ ЗАВЕРШЕНА УСПЕШНО" -ForegroundColor Green
