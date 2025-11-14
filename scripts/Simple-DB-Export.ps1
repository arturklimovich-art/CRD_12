<#
.SYNOPSIS
    ПРОСТОЙ экспорт данных из PostgreSQL
.DESCRIPTION
    Максимально простой и надежный экспорт.
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$OutputPath,
    [string]$Query = "SELECT schemaname, tablename FROM pg_tables LIMIT 10"
)

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$timestamp] [$Level] $Message" -ForegroundColor $(if ($Level -eq "ERROR") { "Red" } elseif ($Level -eq "WARN") { "Yellow" } else { "White" })
}

try {
    Write-Log "🚀 ЗАПУСК ПРОСТОГО ЭКСПОРТА"
    Write-Log "Выходной файл: $OutputPath"
    
    # Создаем директорию
    $outputDir = Split-Path -Path $OutputPath -Parent
    if ($outputDir -and !(Test-Path $outputDir)) {
        New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
        Write-Log "Создана директория: $outputDir"
    }
    
    # Устанавливаем пароль
    $env:PGPASSWORD = "crd12"
    
    # Создаем временный файл с SQL
    $tempFile = [System.IO.Path]::GetTempFileName()
    "COPY ($Query) TO STDOUT WITH (FORMAT CSV, HEADER true, DELIMITER ',');" | Out-File -FilePath $tempFile -Encoding UTF8
    
    Write-Log "Выполнение экспорта..."
    
    # Выполняем psql
    & psql -h localhost -p 5433 -d crd12 -U crd_user -f $tempFile > $OutputPath 2> $null
    
    # Очищаем пароль
    $env:PGPASSWORD = ""
    
    # Удаляем временный файл
    Remove-Item $tempFile -ErrorAction SilentlyContinue
    
    # Исправленная проверка файла
    if (Test-Path $OutputPath) {
        $fileInfo = Get-Item $OutputPath
        if ($fileInfo.Length -gt 0) {
            Write-Log "✅ ЭКСПОРТ УСПЕШЕН! Файл: $OutputPath ($($fileInfo.Length) байт)" -ForegroundColor Green
            exit 0
        } else {
            Write-Log "⚠️  Файл создан, но пустой" -Level "WARN"
            exit 0
        }
    } else {
        Write-Log "❌ Файл не создан" -Level "ERROR"
        exit 1
    }
}
catch {
    Write-Log "❌ Ошибка: $($_.Exception.Message)" -Level "ERROR"
    exit 1
}
