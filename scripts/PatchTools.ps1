# scripts/PatchTools.ps1 - PowerShell CLI for E1-PATCH-MANUAL

# Base URL for Engineer_B API
$EngineerBAPIUrl = "http://localhost:8001"

function Get-EngineerPatch {
    [CmdletBinding(DefaultParameterSetName='List')]
    param(
        [Parameter(ParameterSetName='ById', Mandatory=$true)]
        [string]$Id,
        
        [Parameter(ParameterSetName='List')]
        [ValidateSet("submitted","validated","approved","applying","success","failed","rolled_back")]
        [string]$Status,
        
        [Parameter(ParameterSetName='List')]
        [int]$Limit = 100
    )

    try {
        if ($PSCmdlet.ParameterSetName -eq 'ById') {
            $url = "$EngineerBAPIUrl/api/patches/$Id"
            return Invoke-RestMethod -Uri $url -Method Get
        }
        else {
            $url = "$EngineerBAPIUrl/api/patches"
            $query = @{}
            if ($Status) { $query.status = $Status }
            $query.limit = $Limit
            $qs = ($query.GetEnumerator() | ForEach-Object { "$($_.Key)=$($_.Value)" }) -join "&"
            $fullUrl = "$url`?$qs"
            return Invoke-RestMethod -Uri $fullUrl -Method Get
        }
    }
    catch {
        Write-Error "Error retrieving patch(es): $($_.Exception.Message)"
    }
}

function New-EngineerPatch {
    <#
    .SYNOPSIS
    Upload a new patch to the system

    .PARAMETER File
    Path to .zip/.patch/.py file

    .PARAMETER Author
    Patch author name

    .PARAMETER TaskId
    Related task ID (optional)
    #>

    param(
        [Parameter(Mandatory = $true)]
        [string]$File,

        [Parameter(Mandatory = $true)]
        [string]$Author,

        [string]$TaskId
    )

    if (-not (Test-Path $File)) {
        Write-Error "File not found: $File"
        return
    }

    try {
        $url = "$EngineerBAPIUrl/api/patches"
        $form = @{
            file   = Get-Item $File
            author = $Author
        }
        if ($TaskId) {
            $form.task_id = $TaskId
        }

        $response = Invoke-RestMethod -Uri $url -Method Post -Form $form

        Write-Host "Patch successfully uploaded!" -ForegroundColor Green
        Write-Host "   ID: $($response.id)" -ForegroundColor Yellow
        Write-Host "   Status: $($response.status)" -ForegroundColor Yellow
        if ($response.sha256) {
            Write-Host "   SHA256: $($response.sha256)" -ForegroundColor DarkGray
        }

        return $response
    }
    catch {
        Write-Error "Error uploading patch: $($_.Exception.Message)"
    }
}

function Approve-EngineerPatch {
    <#
    .SYNOPSIS
    Validate and approve a patch

    .DESCRIPTION
    Calls /validate and /approve for the specified patch.
    Returns a token that will be used in Apply-EngineerPatch.
    #>

    param(
        [Parameter(Mandatory = $true)]
        [string]$Id
    )

    try {
        Write-Host "Validating patch $Id..." -ForegroundColor Yellow
        $validateUrl = "$EngineerBAPIUrl/api/patches/$Id/validate"
        $validateResponse = Invoke-RestMethod -Uri $validateUrl -Method Post

        if ($validateResponse.status -ne "validated") {
            Write-Error "Patch validation failed: $($validateResponse.message)"
            return
        }

        Write-Host "Patch validated successfully." -ForegroundColor Green

        Write-Host "Approving patch..." -ForegroundColor Yellow
        $approveUrl = "$EngineerBAPIUrl/api/patches/$Id/approve"
        $approveResponse = Invoke-RestMethod -Uri $approveUrl -Method Post

        Write-Host "Patch approved successfully." -ForegroundColor Green
        if ($approveResponse.token) {
            Write-Host "   Approve token: $($approveResponse.token)" -ForegroundColor Yellow
        }

        return $approveResponse
    }
    catch {
        Write-Error "Error approving patch: $($_.Exception.Message)"
    }
}

function Apply-EngineerPatch {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Id,

        [Parameter(Mandatory = $true)]
        [string]$Token
    )

    try {
        Write-Host "Applying patch $Id..." -ForegroundColor Yellow
        $url = "$EngineerBAPIUrl/api/patches/$Id/apply"

        # важно: backend ждёт JSON-строку, поэтому оборачиваем в кавычки
        $jsonBody = '"' + $Token + '"'

        $response = Invoke-RestMethod -Uri $url -Method Post -Body $jsonBody -ContentType "application/json"

        Write-Host "✅ Patch applied" -ForegroundColor Green
        Write-Host "   status: $($response.status)" -ForegroundColor Yellow
        Write-Host "   sha256: $($response.sha256)" -ForegroundColor DarkGray
        Write-Host "   applied_at: $($response.applied_at)" -ForegroundColor DarkGray

        return $response
    }
    catch {
        Write-Error "Error applying patch: $($_.Exception.Message)"
    }
}

function Show-EngineerPatchStatus {
    <#
    .SYNOPSIS
    Show patches summary

    .DESCRIPTION
    Displays status of recent patches from API
    #>

    try {
        $patches = Get-EngineerPatch -Limit 50

        Write-Host "Patches Summary:" -ForegroundColor Cyan
        Write-Host ("=" * 50) -ForegroundColor Cyan

        $groups = $patches | Group-Object status
        foreach ($g in $groups) {
            $color = switch ($g.Name) {
                "submitted"   { "Yellow" }
                "validated"   { "Blue" }
                "approved"    { "Magenta" }
                "applying"    { "Cyan" }
                "success"     { "Green" }
                "failed"      { "Red" }
                "rolled_back" { "DarkRed" }
                default       { "White" }
            }
            Write-Host ("{0}: {1}" -f $g.Name, $g.Count) -ForegroundColor $color
        }

        Write-Host ("=" * 50) -ForegroundColor Cyan
        Write-Host ("Total patches: {0}" -f ($patches | Measure-Object | Select-Object -ExpandProperty Count)) -ForegroundColor White
    }
    catch {
        Write-Error "Error retrieving patch status: $($_.Exception.Message)"
    }
}

# Module loaded message
Write-Host "PowerShell module PatchTools loaded!" -ForegroundColor Green
Write-Host "Available commands:" -ForegroundColor Yellow
Write-Host "  Get-EngineerPatch" -ForegroundColor White
Write-Host "  New-EngineerPatch" -ForegroundColor White
Write-Host "  Approve-EngineerPatch" -ForegroundColor White
Write-Host "  Apply-EngineerPatch" -ForegroundColor White
Write-Host "  Show-EngineerPatchStatus" -ForegroundColor White
