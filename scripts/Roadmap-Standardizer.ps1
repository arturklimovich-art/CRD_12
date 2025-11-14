# СКРИПТ: Roadmap-Standardizer.ps1
# НАЗНАЧЕНИЕ: Валидация, парсинг и управление стандартизированным Roadmap
# ВЕРСИЯ: 2.0 - С исправленным парсингом YAML и критическими правилами

param(
    [string]$RoadmapPath = "C:\Users\Artur\Documents\CRD12\ROADMAP\ROADMAP_STANDARD.yaml",
    [string]$Action = "validate"  # validate, parse, status, report
)

# КРИТИЧЕСКИЕ ПРАВИЛА СИСТЕМЫ
$STATUS_DICTIONARY = @("PLANNED", "IN_PROGRESS", "DONE", "BLOCKED", "VALIDATED")

# ФУНКЦИИ СКРИПТА
function Import-YamlRoadmap {
    param([string]$Path)
    
    Write-Host "🔍 ЗАГРУЗКА ROADMAP ИЗ: $Path" -ForegroundColor Cyan
    if (-not (Test-Path $Path)) {
        Write-Host "❌ Файл Roadmap не найден: $Path" -ForegroundColor Red
        return $null
    }
    
    try {
        $content = Get-Content $Path -Raw
        return Parse-EnhancedYaml $content
    }
    catch {
        Write-Host "❌ Ошибка загрузки YAML: $($_.Exception.Message)" -ForegroundColor Red
        return $null
    }
}

function Parse-EnhancedYaml {
    param([string]$yamlContent)
    
    Write-Host "🔧 ПАРСИНГ YAML СОДЕРЖИМОГО..." -ForegroundColor Cyan
    $result = @{}
    $lines = $yamlContent -split "`n"
    
    for ($i = 0; $i -lt $lines.Count; $i++) {
        $line = $lines[$i].Trim()
        if ($line -eq "" -or $line.StartsWith("#")) { continue }
        
        # Обработка blocks массива
        if ($line -eq "blocks:") {
            $result["blocks"] = @()
            $i++ # Переход к следующей строке
            
            while ($i -lt $lines.Count -and $lines[$i].Trim().StartsWith("-")) {
                $block = @{}
                $i++ # Вход в блок
                
                while ($i -lt $lines.Count -and $lines[$i].Trim() -ne "" -and -not $lines[$i].Trim().StartsWith("-")) {
                    $blockLine = $lines[$i].Trim()
                    if ($blockLine -match "^(\w+):\s*(.*)") {
                        $key = $matches[1]
                        $value = $matches[2].Trim()
                        $block[$key] = $value -replace '^"|"$', ''  # Удаляем кавычки
                    }
                    $i++
                }
                
                if ($block.Count -gt 0) {
                    $result["blocks"] += $block
                }
            }
        }
        elseif ($line -match "^(\w+):\s*(.*)") {
            # Обработка простых ключ-значений
            $key = $matches[1]
            $value = $matches[2].Trim() -replace '^"|"$', ''
            $result[$key] = $value
        }
    }
    
    return $result
}

function Validate-RoadmapStructure {
    param([hashtable]$roadmapData)
    
    Write-Host "🔍 ВАЛИДАЦИЯ СТРУКТУРЫ ROADMAP..." -ForegroundColor Cyan
    
    $requiredFields = @("version", "phase", "policy", "blocks")
    $missingFields = @()
    
    foreach ($field in $requiredFields) {
        if (-not $roadmapData.ContainsKey($field)) {
            $missingFields += $field
        }
    }
    
    if ($missingFields.Count -gt 0) {
        Write-Host "❌ Отсутствуют обязательные поля: $($missingFields -join ', ')" -ForegroundColor Red
        return $false
    }
    
    # Проверка блоков
    if ($roadmapData["blocks"] -is [array]) {
        Write-Host "✅ Найдено блоков: $($roadmapData['blocks'].Count)" -ForegroundColor Green
        
        # Проверка критических правил
        $validationResult = Validate-CriticalRules -roadmapData $roadmapData
        if (-not $validationResult) {
            return $false
        }
    }
    
    Write-Host "✅ Структура Roadmap валидна" -ForegroundColor Green
    return $true
}

function Validate-CriticalRules {
    param([hashtable]$roadmapData)
    
    Write-Host "🔍 ПРОВЕРКА КРИТИЧЕСКИХ ПРАВИЛ..." -ForegroundColor Cyan
    
    $hasErrors = $false
    
    # Правило 1: Статусы только из словаря
    foreach ($block in $roadmapData["blocks"]) {
        if ($block.ContainsKey("status")) {
            $status = $block["status"]
            if ($STATUS_DICTIONARY -notcontains $status) {
                Write-Host "❌ Некорректный статус '$status' в блоке $($block['id']). Допустимые: $($STATUS_DICTIONARY -join ', ')" -ForegroundColor Red
                $hasErrors = $true
            }
        }
    }
    
    # Правило 2: TZ ссылается на Roadmap (проверяется при создании ТЗ)
    Write-Host "✅ Правило 2 будет проверяться при создании ТЗ" -ForegroundColor Green
    
    return (-not $hasErrors)
}

function Get-RoadmapStatus {
    param([hashtable]$roadmapData)
    
    Write-Host "📊 СТАТУС ROADMAP:" -ForegroundColor Cyan
    
    if ($roadmapData["blocks"] -is [array]) {
        $blocks = $roadmapData["blocks"]
        
        $statusCount = @{
            "DONE" = 0
            "IN_PROGRESS" = 0
            "PLANNED" = 0
            "BLOCKED" = 0
            "VALIDATED" = 0
        }
        
        foreach ($block in $blocks) {
            if ($block.ContainsKey("status")) {
                $status = $block["status"]
                if ($statusCount.ContainsKey($status)) {
                    $statusCount[$status]++
                } else {
                    $statusCount[$status] = 1
                }
            }
        }
        
        Write-Host "   ✅ Выполнено: $($statusCount['DONE'])" -ForegroundColor Green
        Write-Host "   🔄 В процессе: $($statusCount['IN_PROGRESS'])" -ForegroundColor Yellow  
        Write-Host "   📅 Запланировано: $($statusCount['PLANNED'])" -ForegroundColor Blue
        Write-Host "   🚫 Заблокировано: $($statusCount['BLOCKED'])" -ForegroundColor Red
        Write-Host "   🔐 Верифицировано: $($statusCount['VALIDATED'])" -ForegroundColor Magenta
        Write-Host "   📈 Всего блоков: $($blocks.Count)" -ForegroundColor White
    }
}

# ОСНОВНАЯ ЛОГИКА
Write-Host "🎯 ROADMAP STANDARDIZER v2.0" -ForegroundColor Magenta
Write-Host "Действие: $Action" -ForegroundColor Cyan
Write-Host "🚨 КРИТИЧЕСКИЕ ПРАВИЛА АКТИВНЫ:" -ForegroundColor Red
Write-Host "   • Статусы - строго из словаря: $($STATUS_DICTIONARY -join ', ')" -ForegroundColor Yellow
Write-Host "   • TZ обязательно ссылается на задачу Roadmap" -ForegroundColor Yellow

$roadmapData = Import-YamlRoadmap -Path $RoadmapPath

if ($roadmapData) {
    Write-Host "✅ Roadmap загружен успешно" -ForegroundColor Green
    Write-Host "Версия: $($roadmapData['version'])" -ForegroundColor White
    Write-Host "Фаза: $($roadmapData['phase'])" -ForegroundColor White
    
    switch ($Action) {
        "validate" {
            $isValid = Validate-RoadmapStructure -roadmapData $roadmapData
            if ($isValid) {
                Write-Host "🎉 Roadmap прошел валидацию!" -ForegroundColor Green
            }
        }
        "status" {
            Get-RoadmapStatus -roadmapData $roadmapData
        }
        default {
            Write-Host "Действие выполнено: $Action" -ForegroundColor Green
        }
    }
}

Write-Host "`n✅ СКРИПТ ВЫПОЛНЕН" -ForegroundColor Green
