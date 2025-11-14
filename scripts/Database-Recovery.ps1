# Database Recovery Script - Восстановление работоспособности БД
param(
    [switch]$ForceRecreate
)

try {
    Write-Host "🚀 ЗАПУСК ВОССТАНОВЛЕНИЯ БАЗЫ ДАННЫХ..." -ForegroundColor Cyan
    
    # 1. Проверка текущего состояния
    Write-Host "`n🔍 ТЕКУЩЕЕ СОСТОЯНИЕ БАЗ ДАННЫХ:" -ForegroundColor Yellow
    
    $env:PGPASSWORD = "1234"
    $existingDbs = psql -h localhost -p 5433 -U postgres -c "SELECT datname FROM pg_database WHERE datistemplate = false;" -t
    $env:PGPASSWORD = ""
    
    $hasCrd12Db = $existingDbs -match "crd12"
    $hasCrd12PgVectorDb = $existingDbs -match "crd12_pgvector"
    
    Write-Host "   crd12: $(if($hasCrd12Db){'✅'}else{'❌'})" -ForegroundColor $(if($hasCrd12Db){'Green'}else{'Red'})
    Write-Host "   crd12_pgvector: $(if($hasCrd12PgVectorDb){'✅'}else{'❌'})" -ForegroundColor $(if($hasCrd12PgVectorDb){'Green'}else{'Red'})
    
    # 2. Создание недостающих баз данных
    if (-not $hasCrd12Db -or $ForceRecreate) {
        Write-Host "`n📊 СОЗДАНИЕ БАЗЫ ДАННЫХ crd12..." -ForegroundColor Yellow
        $env:PGPASSWORD = "1234"
        psql -h localhost -p 5433 -U postgres -c "CREATE DATABASE crd12;"
        Write-Host "✅ База данных crd12 создана" -ForegroundColor Green
        $env:PGPASSWORD = ""
    }
    
    if (-not $hasCrd12PgVectorDb -or $ForceRecreate) {
        Write-Host "`n📊 СОЗДАНИЕ БАЗЫ ДАННЫХ crd12_pgvector..." -ForegroundColor Yellow
        $env:PGPASSWORD = "1234"
        psql -h localhost -p 5433 -U postgres -c "CREATE DATABASE crd12_pgvector;"
        Write-Host "✅ База данных crd12_pgvector создана" -ForegroundColor Green
        $env:PGPASSWORD = ""
    }
    
    # 3. Создание пользователя и прав
    Write-Host "`n👤 НАСТРОЙКА ПОЛЬЗОВАТЕЛЕЙ И ПРАВ..." -ForegroundColor Yellow
    $env:PGPASSWORD = "1234"
    
    # Создаем пользователя если не существует
    psql -h localhost -p 5433 -U postgres -c "
        DO \$\$
        BEGIN
            IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'crd_user') THEN
                CREATE USER crd_user WITH PASSWORD 'crd12';
            END IF;
        END
        \$\$;"
    
    # Даем права на базы данных
    psql -h localhost -p 5433 -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE crd12 TO crd_user;"
    psql -h localhost -p 5433 -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE crd12_pgvector TO crd_user;"
    
    $env:PGPASSWORD = ""
    Write-Host "✅ Пользователи и права настроены" -ForegroundColor Green
    
    # 4. Проверка восстановления
    Write-Host "`n✅ ПРОВЕРКА ВОССТАНОВЛЕНИЯ..." -ForegroundColor Green
    
    # Проверяем подключение с новым пользователем
    try {
        $env:PGPASSWORD = "crd12"
        $testResult = psql -h localhost -p 5433 -U crd_user -d crd12 -c "SELECT '✅ SUCCESS' as status;" -t
        Write-Host "   Подключение к crd12: $($testResult.Trim())" -ForegroundColor Green
        
        $testResult2 = psql -h localhost -p 5433 -U crd_user -d crd12_pgvector -c "SELECT '✅ SUCCESS' as status;" -t
        Write-Host "   Подключение к crd12_pgvector: $($testResult2.Trim())" -ForegroundColor Green
        $env:PGPASSWORD = ""
    } catch {
        Write-Host "   ❌ Ошибка подключения: $_" -ForegroundColor Red
    }
    
    Write-Host "`n🎯 ВОССТАНОВЛЕНИЕ ЗАВЕРШЕНО" -ForegroundColor Green
    Write-Host "📊 Теперь можно запускать DoV-Runner и другие скрипты" -ForegroundColor Cyan
    
}
catch {
    Write-Host "❌ Ошибка при восстановлении БД: $_" -ForegroundColor Red
}
