# ============================================================================
# Test-ContextScripts.ps1
# Unit tests for context automation scripts
# ============================================================================

Write-Host "🧪 Testing Context Automation Scripts..." -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

$testsPassed = 0
$testsFailed = 0

# Test 1: Check all required files exist
Write-Host "Test 1: Checking required files..." -ForegroundColor Yellow
$requiredFiles = @(
    "Generate-Context-Enhanced.ps1",
    "Load-Context.ps1",
    "Quick-Start.ps1",
    "known_issues.json",
    "README.md"
)

$allFilesExist = $true
foreach ($file in $requiredFiles) {
    $filePath = Join-Path $PSScriptRoot $file
    if (Test-Path $filePath) {
        Write-Host "  ✓ $file exists" -ForegroundColor Green
    } else {
        Write-Host "  ✗ $file missing" -ForegroundColor Red
        $allFilesExist = $false
    }
}

if ($allFilesExist) {
    Write-Host "✅ Test 1 PASSED" -ForegroundColor Green
    $testsPassed++
} else {
    Write-Host "❌ Test 1 FAILED" -ForegroundColor Red
    $testsFailed++
}
Write-Host ""

# Test 2: Validate PowerShell syntax
Write-Host "Test 2: Validating PowerShell syntax..." -ForegroundColor Yellow
$psScripts = @("Generate-Context-Enhanced.ps1", "Load-Context.ps1", "Quick-Start.ps1")
$allSyntaxValid = $true

foreach ($script in $psScripts) {
    $scriptPath = Join-Path $PSScriptRoot $script
    try {
        $errors = $null
        $null = [System.Management.Automation.Language.Parser]::ParseFile($scriptPath, [ref]$null, [ref]$errors)
        if ($errors.Count -eq 0) {
            Write-Host "  ✓ $script syntax valid" -ForegroundColor Green
        } else {
            Write-Host "  ✗ $script syntax error: $($errors[0].Message)" -ForegroundColor Red
            $allSyntaxValid = $false
        }
    } catch {
        Write-Host "  ✗ $script syntax error: $_" -ForegroundColor Red
        $allSyntaxValid = $false
    }
}

if ($allSyntaxValid) {
    Write-Host "✅ Test 2 PASSED" -ForegroundColor Green
    $testsPassed++
} else {
    Write-Host "❌ Test 2 FAILED" -ForegroundColor Red
    $testsFailed++
}
Write-Host ""

# Test 3: Validate JSON syntax
Write-Host "Test 3: Validating JSON files..." -ForegroundColor Yellow
$jsonPath = Join-Path $PSScriptRoot "known_issues.json"
try {
    $json = Get-Content $jsonPath -Raw | ConvertFrom-Json
    Write-Host "  ✓ known_issues.json is valid JSON" -ForegroundColor Green
    
    # Check structure
    $hasRequiredFields = $true
    foreach ($issue in $json) {
        if (-not $issue.issue -or -not $issue.status) {
            Write-Host "  ✗ Issue missing required fields" -ForegroundColor Red
            $hasRequiredFields = $false
        }
    }
    
    if ($hasRequiredFields) {
        Write-Host "  ✓ All issues have required fields" -ForegroundColor Green
        Write-Host "✅ Test 3 PASSED" -ForegroundColor Green
        $testsPassed++
    } else {
        Write-Host "❌ Test 3 FAILED" -ForegroundColor Red
        $testsFailed++
    }
} catch {
    Write-Host "  ✗ known_issues.json is invalid: $_" -ForegroundColor Red
    Write-Host "❌ Test 3 FAILED" -ForegroundColor Red
    $testsFailed++
}
Write-Host ""

# Test 4: Check script parameters
Write-Host "Test 4: Checking script parameters..." -ForegroundColor Yellow

# Generate-Context-Enhanced.ps1
$generateScript = Join-Path $PSScriptRoot "Generate-Context-Enhanced.ps1"
$generateParams = (Get-Command $generateScript).Parameters.Keys
$requiredGenerateParams = @("OutputFile", "User", "LastTask", "SessionSummary")
$hasAllParams = $true

foreach ($param in $requiredGenerateParams) {
    if ($generateParams -contains $param) {
        Write-Host "  ✓ Generate-Context-Enhanced has parameter: $param" -ForegroundColor Green
    } else {
        Write-Host "  ✗ Generate-Context-Enhanced missing parameter: $param" -ForegroundColor Red
        $hasAllParams = $false
    }
}

# Load-Context.ps1
$loadScript = Join-Path $PSScriptRoot "Load-Context.ps1"
$loadParams = (Get-Command $loadScript).Parameters.Keys
if ($loadParams -contains "ContextFile") {
    Write-Host "  ✓ Load-Context has parameter: ContextFile" -ForegroundColor Green
} else {
    Write-Host "  ✗ Load-Context missing parameter: ContextFile" -ForegroundColor Red
    $hasAllParams = $false
}

# Quick-Start.ps1
$quickStartScript = Join-Path $PSScriptRoot "Quick-Start.ps1"
$quickStartParams = (Get-Command $quickStartScript).Parameters.Keys
if ($quickStartParams -contains "ContextFile") {
    Write-Host "  ✓ Quick-Start has parameter: ContextFile" -ForegroundColor Green
} else {
    Write-Host "  ✗ Quick-Start missing parameter: ContextFile" -ForegroundColor Red
    $hasAllParams = $false
}

if ($hasAllParams) {
    Write-Host "✅ Test 4 PASSED" -ForegroundColor Green
    $testsPassed++
} else {
    Write-Host "❌ Test 4 FAILED" -ForegroundColor Red
    $testsFailed++
}
Write-Host ""

# Test 5: Check README structure
Write-Host "Test 5: Checking README.md..." -ForegroundColor Yellow
$readmePath = Join-Path $PSScriptRoot "README.md"
$readmeContent = Get-Content $readmePath -Raw

$requiredSections = @(
    "Быстрый переход между чатами",
    "Завершение текущего чата",
    "Начало нового чата",
    "Generate-Context-Enhanced.ps1",
    "Load-Context.ps1",
    "Quick-Start.ps1"
)

$hasAllSections = $true
foreach ($section in $requiredSections) {
    if ($readmeContent -match [regex]::Escape($section)) {
        Write-Host "  ✓ README contains section: $section" -ForegroundColor Green
    } else {
        Write-Host "  ✗ README missing section: $section" -ForegroundColor Red
        $hasAllSections = $false
    }
}

if ($hasAllSections) {
    Write-Host "✅ Test 5 PASSED" -ForegroundColor Green
    $testsPassed++
} else {
    Write-Host "❌ Test 5 FAILED" -ForegroundColor Red
    $testsFailed++
}
Write-Host ""

# Final summary
Write-Host "═══════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "📊 Test Results:" -ForegroundColor Cyan
Write-Host "   ✅ Passed: $testsPassed" -ForegroundColor Green
Write-Host "   ❌ Failed: $testsFailed" -ForegroundColor Red
Write-Host ""

if ($testsFailed -eq 0) {
    Write-Host "🎉 All tests PASSED!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "⚠️  Some tests FAILED" -ForegroundColor Yellow
    exit 1
}
