Param(
  [string]$BaseUrl = "http://127.0.0.1:4000"
)
Write-Host "LLM status probe: $BaseUrl"
try {
  $models = Invoke-RestMethod -Method GET -Uri "$BaseUrl/v1/models" -TimeoutSec 5
  Write-Host "Models:" ($models.data | ForEach-Object {$_.id}) -Separator ", "
} catch {
  Write-Host "Models endpoint failed: $($_.Exception.Message)"
}

# Simple latency/tok/s probe
$body = @{
  model = "qwen2.5:7b-instruct-q4_K_M"
  messages = @(@{role="user"; content="Say 'ok'"})
  max_tokens = 16
} | ConvertTo-Json -Depth 5
$sw = [System.Diagnostics.Stopwatch]::StartNew()
try {
  $resp = Invoke-RestMethod -Method POST -Uri "$BaseUrl/v1/chat/completions" -Body $body -ContentType "application/json" -TimeoutSec 15
  $sw.Stop()
  $total = $sw.Elapsed.TotalSeconds
  $tokens = $resp.usage.total_tokens
  Write-Host ("Latency(s)={0:N2}  Tokens={1}  ~tok/s={2:N1}" -f $total, $tokens, ($tokens / [Math]::Max($total,0.01)))
} catch {
  Write-Host "Chat completion failed: $($_.Exception.Message)"
}
