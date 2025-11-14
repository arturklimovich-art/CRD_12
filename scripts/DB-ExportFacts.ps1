<#
.SYNOPSIS
    Экспорт данных из PostgreSQL в CSV-файл
.DESCRIPTION
    Надёжный неинтерактивный механизм выгрузки данных из PostgreSQL в CSV-файлы
    с исправлением проблемы аргументов psql.
#>

param(
    [Parameter(ParameterSetName="Query")]
    [string]$Query,
    
    [Parameter(ParameterSetName="Table")]
    [string]$TableName,
    
    [Parameter(Mandatory=$true)]
    [string]$OutputPath,
    
    [string]$Host = "localhost",
    [int]$Port = 5433,
    [string]$Database = "crd12",
    [string]$User = "crd_user",
    [string]$Password = "crd12",
    
    [ValidateSet('Simple', 'File')]
    [string]$Method = 'Simple'
)

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$timestamp] [$Level] $Message" -ForegroundColor $(if ($Level -eq "ERROR") { "Red" } elseif ($Level -eq "WARN") { "Yellow" } else { "White" })
}

function Test-PostgreSQLConnection {
    param([string]$Host, [int]$Port)
    
    try {
        Write-Log "Проверка подключения к PostgreSQL: $Host`:$Port"
        
        $tcpTest = New-Object System.Net.Sockets.TcpClient
        $connectionResult = $tcpTest.BeginConnect($Host, $Port, $null, $null)
        $success = $connectionResult.AsyncWaitHandle.WaitOne(3000, $false)
        
        if ($success) {
            $tcpTest.EndConnect($connectionResult)
            $tcpTest.Close()
            Write-Log "✅ Подключение к $Host`:$Port успешно" -ForegroundColor Green
            return $true
        } else {
            $tcpTest.Close()
            Write-Log "❌ Не удалось подключиться к $Host`:$Port" -Level "ERROR"
            return $false
        }
    }
    catch {
        Write-Log "❌ Ошибка при проверке подключения: $($_.Exception.Message)" -Level "ERROR"
        return $false
    }
}

function Test-PostgreSQLAuth {
    param([string]$Host, [int]$Port, [string]$Database, [string]$User, [string]$Password)
    
    try {
        Write-Log "Проверка аутентификации PostgreSQL: $User@$Database"
        
        # Используем переменные окружения для пароля
        $env:PGPASSWORD = $Password
        
        $testResult = & psql -h $Host -p $Port -d $Database -U $User -t -c "SELECT 1;" 2>&1
        
        if ($LASTEXITCODE -eq 0 -and $testResult -match "1") {
            Write-Log "✅ Аутентификация успешна" -ForegroundColor Green
            return $true
        } else {
            Write-Log "❌ Ошибка аутентификации: $testResult" -Level "ERROR"
            return $false
        }
    }
    catch {
        Write-Log "❌ Ошибка при проверке аутентификации: $($_.Exception.Message)" -Level "ERROR"
        return $false
    }
    finally {
        # Очищаем пароль из переменных окружения
        $env:PGPASSWORD = ""
    }
}

function Test-TableExists {
    param([string]$Host, [int]$Port, [string]$Database, [string]$User, [string]$Password, [string]$TableName)
    
    try {
        Write-Log "Проверка существования таблицы: $TableName"
        
        $env:PGPASSWORD = $Password
        
        if ($TableName -match "(.+)\.(.+)") {
            $schema = $Matches[1]
            $table = $Matches[2]
            $testQuery = "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = '$schema' AND table_name = '$table');"
        } else {
            $testQuery = "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '$TableName');"
        }
        
        $result = & psql -h $Host -p $Port -d $Database -U $User -t -c $testQuery 2>&1
        $env:PGPASSWORD = ""
        
        if ($LASTEXITCODE -eq 0 -and $result -match 't') {
            Write-Log "✅ Таблица $TableName существует" -ForegroundColor Green
            return $true
        } else {
            Write-Log "❌ Таблица $TableName не существует" -Level "ERROR"
            return $false
        }
    }
    catch {
        Write-Log "❌ Ошибка при проверке таблицы: $($_.Exception.Message)" -Level "ERROR"
        $env:PGPASSWORD = ""
        return $false
    }
}

function Get-ExportQuery {
    param([string]$Query, [string]$TableName)
    
    if ($TableName) {
        Write-Log "Экспорт таблицы: $TableName"
        return "COPY $TableName TO STDOUT WITH (FORMAT CSV, HEADER true, DELIMITER ',');"
    }
    elseif ($Query) {
        Write-Log "Использование пользовательского запроса"
        $cleanQuery = $Query.Trim()
        if ($cleanQuery.EndsWith(';')) {
            $cleanQuery = $cleanQuery.Substring(0, $cleanQuery.Length - 1)
        }
        return "COPY ($cleanQuery) TO STDOUT WITH (FORMAT CSV, HEADER true, DELIMITER ',');"
    }
    else {
        throw "Не указан Query или TableName"
    }
}

function Export-UsingSimple {
    param([string]$Host, [int]$Port, [string]$Database, [string]$User, [string]$Password, [string]$Query, [string]$OutputPath)
    
    try {
        Write-Log "Подготовка экспорта упрощенным методом"
        
        # Устанавливаем пароль в переменную окружения
        $env:PGPASSWORD = $Password
        
        Write-Log "Выполнение: psql с параметрами подключения"
        Write-Log "Выходной файл: $OutputPath"
        
        # Создаем временный файл с SQL запросом
        $tempFile = [System.IO.Path]::GetTempFileName()
        $Query | Out-File -FilePath $tempFile -Encoding UTF8
        Write-Log "SQL запрос сохранен во временный файл: $tempFile"
        
        # Выполняем psql с отдельными параметрами
        & psql -h $Host -p $Port -d $Database -U $User -f $tempFile > $OutputPath 2> $null
        
        # Проверяем результат
        if ($LASTEXITCODE -ne 0) {
            throw "psql завершился с кодом ошибки: $LASTEXITCODE"
        }
        
        Write-Log "✅ Данные успешно записаны в файл" -ForegroundColor Green
        
        # Удаляем временный файл
        Remove-Item $tempFile -ErrorAction SilentlyContinue
        Write-Log "Временный файл удален: $tempFile"
    }
    catch {
        Write-Log "❌ Ошибка в упрощенном методе: $($_.Exception.Message)" -Level "ERROR"
        # Пытаемся очистить временные файлы
        if ($tempFile -and (Test-Path $tempFile)) {
            Remove-Item $tempFile -ErrorAction SilentlyContinue
        }
        throw
    }
    finally {
        # Всегда очищаем пароль
        $env:PGPASSWORD = ""
    }
}

# Основная логика
try {
    Write-Log "🚀 ЗАПУСК ЭКСПОРТА ДАННЫХ ИЗ POSTGRESQL"
    Write-Log "Метод: $Method"
    Write-Log "Выходной файл: $OutputPath"
    Write-Log "Подключение: $User@$Host`:$Port/$Database"
    
    if (-not $OutputPath) {
        throw "Параметр OutputPath обязателен"
    }
    
    $outputDir = Split-Path -Path $OutputPath -Parent
    if ($outputDir -and !(Test-Path $outputDir)) {
        New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
        Write-Log "Создана директория: $outputDir"
    }
    
    # Проверяем подключение к БД
    if (!(Test-PostgreSQLConnection -Host $Host -Port $Port)) {
        Write-Log "❌ Ошибка подключения к PostgreSQL. Код ошибки: 0x00002742/10050" -Level "ERROR"
        exit 10050
    }
    
    # Проверяем аутентификацию
    if (!(Test-PostgreSQLAuth -Host $Host -Port $Port -Database $Database -User $User -Password $Password)) {
        Write-Log "❌ Ошибка аутентификации PostgreSQL. Код ошибки: 10052" -Level "ERROR"
        exit 10052
    }
    
    # Если указана таблица, проверяем её существование
    if ($TableName -and !(Test-TableExists -Host $Host -Port $Port -Database $Database -User $User -Password $Password -TableName $TableName)) {
        Write-Log "❌ Таблица $TableName не найдена. Код ошибки: 10051" -Level "ERROR"
        exit 10051
    }
    
    $exportQuery = Get-ExportQuery -Query $Query -TableName $TableName
    Write-Log "SQL запрос подготовлен"
    
    # Используем упрощенный метод
    Write-Log "Использование упрощенного метода"
    Export-UsingSimple -Host $Host -Port $Port -Database $Database -User $User -Password $Password -Query $exportQuery -OutputPath $OutputPath
    
    # Проверяем результат
    if (Test-Path $OutputPath -ErrorAction SilentlyContinue) {
        $fileSize = (Get-Item $OutputPath).Length
        $lineCount = (Get-Content $OutputPath | Measure-Object -Line).Lines
        $rowCount = if ($lineCount -gt 1) { $lineCount - 1 } else { 0 }
        
        if ($fileSize -gt 0) {
            Write-Log "✅ ЭКСПОРТ УСПЕШНО ЗАВЕРШЕН!" -ForegroundColor Green
            Write-Log "📊 Файл: $OutputPath ($fileSize байт, $rowCount строк данных)" -ForegroundColor Cyan
            exit 0
        } else {
            Write-Log "⚠️  Файл создан, но пустой. Возможно, таблица пуста." -Level "WARN"
            exit 0
        }
    } else {
        Write-Log "❌ Файл не создан: $OutputPath" -Level "ERROR"
        exit 1
    }
}
catch {
    Write-Log "❌ Критическая ошибка при экспорте: $($_.Exception.Message)" -Level "ERROR"
    exit 1
}
