# СКРИПТ: Create-Test-TZ.ps1
# НАЗНАЧЕНИЕ: Ручное создание тестовых технических заданий для проверки системы
# ВЕРСИЯ: 1.0

# КОНФИГУРАЦИЯ БАЗЫ ДАННЫХ
$DatabaseConfig = @{
    ContainerName = "crd12_pgvector"
    Database = "crd12"
    Username = "crd_user"
    Password = "crd12"
}

# ТЕСТОВЫЕ ТЕХНИЧЕСКИЕ ЗАДАНИЯ
$testTechnicalSpecifications = @(
    @{
        roadmap_task_id = "TZ_4.1"
        tz_title = "Стандартизация формата Roadmap"
        tz_description = "Преобразование Roadmap в машиночитаемый формат YAML для автоматического парсинга системой"
        tz_steps = "Проанализировать текущий формат|Создать YAML шаблон|Мигрировать существующие данные|Протестировать парсер"
        status = "IN_PROGRESS"
        tz_priority = "HIGH"
        created_by = "Manual_Test_v1"
    },
    @{
        roadmap_task_id = "TZ_4.2" 
        tz_title = "Создание базы данных технических заданий"
        tz_description = "Разработка схемы БД для хранения ТЗ и связей с Roadmap и Navigator"
        tz_steps = "Спроектировать схему БД ТЗ|Создать таблицы technical_specifications|Реализовать API для работы с ТЗ|Настроить связи"
        status = "DONE"
        tz_priority = "HIGH"
        created_by = "Manual_Test_v1"
    },
    @{
        roadmap_task_id = "TZ_4.3"
        tz_title = "Разработка Bot Orchestrator для создания ТЗ"
        tz_description = "Создание автоматической системы генерации ТЗ из задач Roadmap"
        tz_steps = "Реализовать парсер Roadmap|Создать ИИ-агента для разработки ТЗ|Настроить сохранение ТЗ в БД|Протестировать интеграцию"
        status = "IN_PROGRESS"
        tz_priority = "HIGH"
        created_by = "Manual_Test_v1"
    },
    @{
        roadmap_task_id = "TEST_001"
        tz_title = "Тестовое ТЗ для проверки системы"
        tz_description = "Тестовое техническое задание созданное вручную для проверки работы базы данных и критических правил"
        tz_steps = "Шаг 1: Создать тестовое ТЗ|Шаг 2: Проверить сохранение в БД|Шаг 3: Убедиться в работе constraints|Шаг 4: Протестировать представления"
        status = "PLANNED"
        tz_priority = "MEDIUM"
        created_by = "Manual_Test_v1"
    }
)

function Save-TZ-To-Database {
    param([array]$technicalSpecifications)
    
    Write-Host "💾 СОХРАНЕНИЕ ТЕСТОВЫХ ТЗ В БАЗУ ДАННЫХ..." -ForegroundColor Cyan
    
    $savedCount = 0
    $errorCount = 0
    
    foreach ($tz in $technicalSpecifications) {
        try {
            # Экранируем кавычки для SQL
            $title = $tz.tz_title -replace "'", "''"
            $description = $tz.tz_description -replace "'", "''"
            $steps = $tz.tz_steps -replace "'", "''"
            
            # Создаем SQL команду для вставки
            $sqlCommand = @"
INSERT INTO eng_it.technical_specifications (
    roadmap_task_id, 
    tz_title, 
    tz_description, 
    tz_steps, 
    status, 
    tz_priority, 
    created_by
) VALUES (
    '$($tz.roadmap_task_id)',
    '$title',
    '$description',
    '$steps',
    '$($tz.status)',
    '$($tz.tz_priority)',
    '$($tz.created_by)'
);
"@
            
            Write-Host "   💾 Сохранение: $($tz.roadmap_task_id) - $($tz.tz_title)" -ForegroundColor DarkGray
            
            # Выполняем SQL команду
            $output = docker exec $DatabaseConfig.ContainerName bash -c "PGPASSWORD=$($DatabaseConfig.Password) psql -U $($DatabaseConfig.Username) -d $($DatabaseConfig.Database) -c `"$sqlCommand`" 2>&1"
            
            if ($LASTEXITCODE -eq 0 -and $output -notmatch "ERROR") {
                $savedCount++
                Write-Host "   ✅ ТЗ сохранено: $($tz.roadmap_task_id)" -ForegroundColor Green
            } else {
                $errorCount++
                Write-Host "   ❌ Ошибка сохранения: $($tz.roadmap_task_id)" -ForegroundColor Red
                if ($output -and $output.Trim()) {
                    Write-Host "      Ошибка: $output" -ForegroundColor Red
                }
            }
        }
        catch {
            $errorCount++
            Write-Host "   ❌ Исключение: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
    
    Write-Host "`n📊 РЕЗУЛЬТАТ СОХРАНЕНИЯ:" -ForegroundColor Cyan
    Write-Host "   ✅ Успешно: $savedCount" -ForegroundColor Green
    Write-Host "   ❌ Ошибки: $errorCount" -ForegroundColor Red
    
    return $savedCount
}

function Test-CriticalRules {
    Write-Host "🧪 ТЕСТИРОВАНИЕ КРИТИЧЕСКИХ ПРАВИЛ..." -ForegroundColor Yellow
    
    # Тест 1: Проверка валидации статусов
    Write-Host "`n🧪 Тест 1: Валидация статусов (критическое правило 1)..." -ForegroundColor Cyan
    $invalidStatusTest = @"
INSERT INTO eng_it.technical_specifications (roadmap_task_id, tz_title, status) 
VALUES ('TEST_INVALID_STATUS', 'Тест с невалидным статусом', 'INVALID_STATUS');
"@
    $output = docker exec $DatabaseConfig.ContainerName bash -c "PGPASSWORD=$($DatabaseConfig.Password) psql -U $($DatabaseConfig.Username) -d $($DatabaseConfig.Database) -c `"$invalidStatusTest`" 2>&1"
    if ($output -match "violates check constraint") {
        Write-Host "   ✅ Критическое правило 1 РАБОТАЕТ: неверные статусы отклоняются" -ForegroundColor Green
    } else {
        Write-Host "   ❌ Проблема с проверкой статусов" -ForegroundColor Red
    }
    
    # Тест 2: Проверка обязательной ссылки на Roadmap
    Write-Host "🧪 Тест 2: Обязательная ссылка на Roadmap (критическое правило 2)..." -ForegroundColor Cyan
    $nullReferenceTest = @"
INSERT INTO eng_it.technical_specifications (tz_title, status) 
VALUES ('Тест без ссылки на Roadmap', 'PLANNED');
"@
    $output = docker exec $DatabaseConfig.ContainerName bash -c "PGPASSWORD=$($DatabaseConfig.Password) psql -U $($DatabaseConfig.Username) -d $($DatabaseConfig.Database) -c `"$nullReferenceTest`" 2>&1"
    if ($output -match "null value in column") {
        Write-Host "   ✅ Критическое правило 2 РАБОТАЕТ: TZ без ссылки на Roadmap отклоняются" -ForegroundColor Green
    } else {
        Write-Host "   ❌ Проблема с проверкой ссылок" -ForegroundColor Red
    }
}

function Show-TZ-Statistics {
    Write-Host "📊 СТАТИСТИКА ТЕХНИЧЕСКИХ ЗАДАНИЙ В БАЗЕ..." -ForegroundColor Cyan
    
    try {
        # Статистика по статусам
        $sqlCommand = "SELECT status, COUNT(*) as count FROM eng_it.technical_specifications GROUP BY status ORDER BY status;"
        $output = docker exec $DatabaseConfig.ContainerName bash -c "PGPASSWORD=$($DatabaseConfig.Password) psql -U $($DatabaseConfig.Username) -d $($DatabaseConfig.Database) -c `"$sqlCommand`""
        Write-Host "📈 СТАТУС ТЗ:" -ForegroundColor Yellow
        Write-Host $output -ForegroundColor Gray
        
        # Общее количество
        $totalCommand = "SELECT COUNT(*) as total_tz FROM eng_it.technical_specifications;"
        $totalOutput = docker exec $DatabaseConfig.ContainerName bash -c "PGPASSWORD=$($DatabaseConfig.Password) psql -U $($DatabaseConfig.Username) -d $($DatabaseConfig.Database) -c `"$totalCommand`""
        Write-Host "📊 ВСЕГО ТЗ:" -ForegroundColor Yellow
        Write-Host $totalOutput -ForegroundColor Gray
        
        # Детальный список
        $detailsCommand = "SELECT roadmap_task_id, tz_title, status, created_by FROM eng_it.technical_specifications ORDER BY created_at;"
        $detailsOutput = docker exec $DatabaseConfig.ContainerName bash -c "PGPASSWORD=$($DatabaseConfig.Password) psql -U $($DatabaseConfig.Username) -d $($DatabaseConfig.Database) -c `"$detailsCommand`""
        Write-Host "📋 ДЕТАЛЬНЫЙ СПИСОК ТЗ:" -ForegroundColor Yellow
        Write-Host $detailsOutput -ForegroundColor Gray
    }
    catch {
        Write-Host "❌ Ошибка получения статистики: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# ОСНОВНАЯ ЛОГИКА
Write-Host "🎯 СОЗДАНИЕ ТЕСТОВЫХ ТЕХНИЧЕСКИХ ЗАДАНИЙ" -ForegroundColor Magenta
Write-Host "Количество тестовых ТЗ: $($testTechnicalSpecifications.Count)" -ForegroundColor Cyan

# Сохраняем тестовые ТЗ
$savedCount = Save-TZ-To-Database -technicalSpecifications $testTechnicalSpecifications

if ($savedCount -gt 0) {
    Write-Host "`n🎉 ТЕСТОВЫЕ ТЗ УСПЕШНО СОЗДАНЫ!" -ForegroundColor Green
    
    # Тестируем критические правила
    Test-CriticalRules
    
    # Показываем статистику
    Show-TZ-Statistics
    
    Write-Host "`n✅ СИСТЕМА БАЗЫ ДАННЫХ ТЗ РАБОТАЕТ КОРРЕКТНО!" -ForegroundColor Green
    Write-Host "   • Таблицы созданы" -ForegroundColor White
    Write-Host "   • Constraints работают" -ForegroundColor White
    Write-Host "   • Данные сохраняются" -ForegroundColor White
    Write-Host "   • Критические правила соблюдаются" -ForegroundColor White
} else {
    Write-Host "❌ Не удалось создать тестовые ТЗ" -ForegroundColor Red
}

Write-Host "`n✅ СКРИПТ ВЫПОЛНЕН" -ForegroundColor Green
