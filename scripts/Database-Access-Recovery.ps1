# Правильное восстановление доступа к существующей БД
param()

try {
    Write-Host "🔐 ВОССТАНОВЛЕНИЕ ДОСТУПА К СУЩЕСТВУЮЩЕЙ БАЗЕ ДАННЫХ..." -ForegroundColor Cyan
    
    # Используем найденные правильные данные
    $postgresPassword = "postgres"
    $existingDatabase = "crd12"
    
    Write-Host "✅ Используем базу данных: $existingDatabase" -ForegroundColor Green
    Write-Host "✅ Пароль postgres: $postgresPassword" -ForegroundColor Green
    
    # 1. Проверяем существование пользователя crd_user
    Write-Host "
👤 ПРОВЕРКА ПОЛЬЗОВАТЕЛЯ crd_user..." -ForegroundColor Yellow
    $env:PGPASSWORD = $postgresPassword
    $userExists = psql -h localhost -p 5433 -U postgres -d $existingDatabase -c "
        SELECT 1 FROM pg_roles WHERE rolname = 'crd_user';" -t
    
    if ($userExists -and $userExists.Trim() -eq "1") {
        Write-Host "✅ Пользователь crd_user существует" -ForegroundColor Green
        
        # Пробуем подключиться с паролем crd12
        Write-Host "🔑 Тестирование подключения crd_user..." -ForegroundColor Gray
        $env:PGPASSWORD = "crd12"
        $testCrdUser = psql -h localhost -p 5433 -U crd_user -d $existingDatabase -c "SELECT 'SUCCESS' as status;" -t 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ crd_user подключен с паролем 'crd12'" -ForegroundColor Green
        } else {
            Write-Host "❌ crd_user не подключается с паролем 'crd12'" -ForegroundColor Red
            Write-Host "💡 Сброс пароля для crd_user..." -ForegroundColor Yellow
            $env:PGPASSWORD = $postgresPassword
            psql -h localhost -p 5433 -U postgres -c "ALTER USER crd_user WITH PASSWORD 'crd12';"
            Write-Host "✅ Пароль crd_user сброшен на 'crd12'" -ForegroundColor Green
        }
    } else {
        Write-Host "❌ Пользователь crd_user не существует" -ForegroundColor Red
        Write-Host "👤 Создаем пользователя crd_user..." -ForegroundColor Yellow
        $env:PGPASSWORD = $postgresPassword
        psql -h localhost -p 5433 -U postgres -c "CREATE USER crd_user WITH PASSWORD 'crd12';"
        psql -h localhost -p 5433 -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE $existingDatabase TO crd_user;"
        Write-Host "✅ Пользователь crd_user создан" -ForegroundColor Green
    }
    
    $env:PGPASSWORD = ""
    
    # 2. Финальная проверка
    Write-Host "
🎯 ФИНАЛЬНАЯ ПРОВЕРКА ДОСТУПА..." -ForegroundColor Green
    $env:PGPASSWORD = "crd12"
    $finalTest = psql -h localhost -p 5433 -U crd_user -d $existingDatabase -c "
        SELECT COUNT(*) as table_count 
        FROM information_schema.tables 
        WHERE table_schema NOT IN ('information_schema', 'pg_catalog');" -t
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ ДОСТУП ВОССТАНОВЛЕН!" -ForegroundColor Green
        Write-Host "📊 Таблиц в базе: $($finalTest.Trim())" -ForegroundColor Cyan
    } else {
        Write-Host "❌ Проблемы с доступом остались" -ForegroundColor Red
    }
    $env:PGPASSWORD = ""
    
}
catch {
    Write-Host "❌ Ошибка при восстановлении: $_" -ForegroundColor Red
}
