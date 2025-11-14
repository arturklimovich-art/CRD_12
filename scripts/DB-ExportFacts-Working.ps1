<#
.SYNOPSIS
    РАБОЧИЙ экспорт данных из PostgreSQL в CSV-файл
.DESCRIPTION
    Надёжный механизм выгрузки данных с исправлением всех проблем.
#>

param(
    [Parameter(ParameterSetName="Query")]
    [string]$Query,
    
    [Parameter(ParameterSetName="Table")]
    [string]$TableName,
    
    [Parameter(Mandatory=$true)]
    [string]$OutputPath,
    
    [string]$DbHost = "localhost",
    [int]$DbPort = 5433,
    [string]$DbName = "crd12",
    [string]$DbUser = "crd_user",
    [string]$DbPassword = "crd12"
)

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$timestamp] [$Level] $Message" -ForegroundColor $(if ($Level -eq "ERROR") { "Red" } elseif ($Level -eq "WARN") { "Yellow" } else { "White" })
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

# Основная логика
try {
    Write-Log "🚀 ЗАПУСК ЭКСПОРТА ДАННЫХ ИЗ POSTGRESQL"
    Write-Log "Выходной файл: $OutputPath"
    Write-Log "Подключение: $DbUser@$DbHost`:$DbPort/$DbName"
    
    if (-not $OutputPath) {
        throw "Параметр OutputPath обязателен"
    }
    
    $outputDir = Split-Path -Path $OutputPath -Parent
    if ($outputDir -and !(Test-Path $outputDir)) {
        New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
        Write-Log "Создана директория: $outputDir"
    }
    
    $exportQuery = Get-ExportQuery -Query $Query -TableName $TableName
    Write-Log "SQL запрос подготовлен: $exportQuery"
    
    # Устанавливаем пароль
    $env:PGPASSWORD = $DbPassword
    
    # Создаем временный файл с SQL
    $tempFile = [System.IO.Path]::GetTempFileName()
    $exportQuery | Out-File -FilePath $tempFile -Encoding UTF8
    Write-Log "SQL запрос сохранен во временный файл: $tempFile"
    
    Write-Log "Выполнение экспорта через psql..."
    
    # Выполняем psql с отдельными параметрами
    & psql -h $DbHost -p $DbPort -d $DbName -U $DbUser -f $tempFile > $OutputPath 2> $null
    
    # Очищаем пароль
    $env:PGPASSWORD = ""
    
    # Удаляем временный файл
    Remove-Item $tempFile -ErrorAction SilentlyContinue
    Write-Log "Временный файл удален"
    
    # Проверяем результат
    if (Test-Path $OutputPath) {
        $fileInfo = Get-Item $OutputPath
        $lineCount = (Get-Content $OutputPath | Measure-Object -Line).Lines
        $rowCount = if ($lineCount -gt 1) { $lineCount - 1 } else { 0 }
        
        if ($fileInfo.Length -gt 0) {
            Write-Log "✅ ЭКСПОРТ УСПЕШНО ЗАВЕРШЕН!" -ForegroundColor Green
            Write-Log "📊 Файл: $OutputPath ($($fileInfo.Length) байт, $rowCount строк данных)" -ForegroundColor Cyan
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
    # Очищаем пароль в случае ошибки
    $env:PGPASSWORD = ""
    exit 1
}
