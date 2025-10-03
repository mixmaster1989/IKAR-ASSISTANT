param(
    [string]$BaseUrl = "http://localhost:6666",
    [switch]$Verbose
)

Write-Host "Testing Admin API functions" -ForegroundColor Green
Write-Host "Base URL: $BaseUrl" -ForegroundColor Cyan
Write-Host "=" * 50

function Invoke-ApiTest {
    param(
        [string]$Method,
        [string]$Endpoint,
        [hashtable]$Body = $null,
        [string]$Description
    )
    
    Write-Host "`nTest: $Description" -ForegroundColor Yellow
    Write-Host "$Method $Endpoint" -ForegroundColor Gray
    
    try {
        $params = @{
            Uri = "$BaseUrl$Endpoint"
            Method = $Method
            ContentType = "application/json"
        }
        
        if ($Body) {
            $jsonBody = $Body | ConvertTo-Json -Depth 10
            $params.Body = $jsonBody
            if ($Verbose) {
                Write-Host "Request body: $jsonBody" -ForegroundColor Gray
            }
        }
        
        $response = Invoke-RestMethod @params
        Write-Host "Success (200)" -ForegroundColor Green
        
        if ($Verbose) {
            Write-Host "Response:" -ForegroundColor Gray
            $response | ConvertTo-Json -Depth 5 | Write-Host
        } else {
            if ($response.groups) {
                Write-Host "Groups found: $($response.groups.Count)" -ForegroundColor Cyan
            }
            if ($response.status) {
                Write-Host "Status: $($response.status)" -ForegroundColor Cyan
            }
            if ($response.enabled -ne $null) {
                Write-Host "Enabled: $($response.enabled)" -ForegroundColor Cyan
            }
        }
        
        return $response
    }
    catch {
        $statusCode = $_.Exception.Response.StatusCode.value__
        $errorMessage = $_.Exception.Message
        
        Write-Host "Error ($statusCode): $errorMessage" -ForegroundColor Red
        
        if ($_.Exception.Response) {
            try {
                $errorStream = $_.Exception.Response.GetResponseStream()
                $reader = New-Object System.IO.StreamReader($errorStream)
                $errorBody = $reader.ReadToEnd()
                Write-Host "Error details: $errorBody" -ForegroundColor Red
            }
            catch {
                Write-Host "Could not get error details" -ForegroundColor Red
            }
        }
        
        return $null
    }
}

Write-Host "`nChecking server availability..." -ForegroundColor Blue
try {
    $healthCheck = Invoke-RestMethod -Uri "$BaseUrl/" -Method GET -TimeoutSec 5
    Write-Host "Server is available" -ForegroundColor Green
}
catch {
    Write-Host "Server is not available! Make sure server is running on $BaseUrl" -ForegroundColor Red
    Write-Host "To start server run: cd backend; python main.py" -ForegroundColor Yellow
    exit 1
}

$groups = Invoke-ApiTest -Method "GET" -Endpoint "/api/admin/groups" -Description "Get groups list"

$debugInfo = Invoke-ApiTest -Method "GET" -Endpoint "/api/admin/debug_groups" -Description "Get debug groups info"

$channelStatus = Invoke-ApiTest -Method "GET" -Endpoint "/api/admin/channel_status" -Description "Get channel status"

if ($groups -and $groups.groups -and $groups.groups.Count -gt 0) {
    $firstGroup = $groups.groups[0]
    if ($firstGroup.users -and $firstGroup.users.Count -gt 0) {
        $firstUser = $firstGroup.users[0]
        
        $setNameBody = @{
            chat_id = $firstGroup.chat_id
            user_id = $firstUser.user_id
            name = "Test_Name_$(Get-Date -Format 'HHmmss')"
        }
        
        Invoke-ApiTest -Method "POST" -Endpoint "/api/admin/set_name" -Body $setNameBody -Description "Set user name"
    } else {
        Write-Host "Skip set name test - no users in groups" -ForegroundColor Yellow
    }
} else {
    Write-Host "Skip set name test - no groups" -ForegroundColor Yellow
}

$toggleBody = @{
    enabled = $true
}
Invoke-ApiTest -Method "POST" -Endpoint "/api/admin/channel_toggle" -Body $toggleBody -Description "Enable channel"

$toggleBody = @{
    enabled = $false
}
Invoke-ApiTest -Method "POST" -Endpoint "/api/admin/channel_toggle" -Body $toggleBody -Description "Disable channel"

if ($groups -and $groups.groups -and $groups.groups.Count -gt 0) {
    $firstGroup = $groups.groups[0]
    
    $createSoulBody = @{
        chat_id = $firstGroup.chat_id
    }
    
    Write-Host "`nWarning: Soul creation test may take time and requires LLM API" -ForegroundColor Yellow
    $createSoul = Read-Host "Run soul creation test? (y/N)"
    
    if ($createSoul -eq "y" -or $createSoul -eq "Y") {
        Invoke-ApiTest -Method "POST" -Endpoint "/api/admin/create_soul" -Body $createSoulBody -Description "Create group soul"
    } else {
        Write-Host "Skip soul creation test" -ForegroundColor Yellow
    }
} else {
    Write-Host "Skip soul creation test - no groups" -ForegroundColor Yellow
}

Write-Host "`n" + "=" * 50
Write-Host "Testing completed!" -ForegroundColor Green
Write-Host "Use -Verbose flag for detailed output" -ForegroundColor Cyan
Write-Host "Example: .\test_admin_api.ps1 -Verbose" -ForegroundColor Cyan
