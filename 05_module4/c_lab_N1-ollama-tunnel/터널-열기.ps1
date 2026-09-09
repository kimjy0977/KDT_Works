# n8n → 내 Ollama 터널 열기
# 쓰는 법: 파워셸에서  .\터널-열기.ps1
# 끄는 법: .\터널-닫기.ps1  (또는 이 창에서 Ctrl+C)

$ErrorActionPreference = "Stop"
$cf  = "C:\Program Files (x86)\cloudflared\cloudflared.exe"
$log = "$env:TEMP\cf-ollama.log"

# 0) Ollama 살아 있나
try {
  Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -TimeoutSec 5 | Out-Null
  Write-Host "  Ollama 정상" -ForegroundColor Green
} catch {
  Write-Host "  X Ollama 가 안 떠 있습니다. 먼저 Ollama 를 실행하세요." -ForegroundColor Red
  exit 1
}

# 1) 이미 떠 있으면 정리
Get-Process cloudflared -ErrorAction SilentlyContinue | Stop-Process -Force
if (Test-Path $log) { Remove-Item $log -Force }

# 2) 터널 시작
#    --http-host-header 가 필요한 이유: Ollama 는 낯선 Host 헤더를 403 으로 거부한다.
#    이거 빼면 무조건 403 이다.
Start-Process -FilePath $cf -WindowStyle Hidden -ArgumentList `
  "tunnel","--url","http://localhost:11434","--http-host-header","localhost:11434","--logfile",$log | Out-Null

# 3) 주소 나올 때까지 대기
Write-Host "  터널 여는 중..." -NoNewline
$url = $null
for ($i = 0; $i -lt 30; $i++) {
  Start-Sleep -Seconds 1
  Write-Host "." -NoNewline
  if (Test-Path $log) {
    $m = Select-String -Path $log -Pattern "https://[a-z0-9-]+\.trycloudflare\.com" -ErrorAction SilentlyContinue
    if ($m) { $url = $m.Matches[0].Value; break }
  }
}
Write-Host ""

if (-not $url) {
  Write-Host "  X 주소를 못 받았습니다. 로그: $log" -ForegroundColor Red
  exit 1
}

# 4) 진짜 닿는지 확인 (주소만 받고 안 되는 경우가 있다)
try {
  $r = Invoke-RestMethod -Uri "$url/v1/models" -TimeoutSec 25
  $models = ($r.data | ForEach-Object { $_.id }) -join ", "
  Write-Host "  통신 확인 · 모델: $models" -ForegroundColor Green
} catch {
  Write-Host "  ! 주소는 받았지만 응답이 없습니다: $($_.Exception.Message)" -ForegroundColor Yellow
}

$base = "$url/v1"
Write-Host ""
Write-Host "  === n8n 크리덴셜의 Base URL 에 붙여넣으세요 ===" -ForegroundColor Cyan
Write-Host "  $base" -ForegroundColor White
try { Set-Clipboard -Value $base; Write-Host "  (클립보드에 복사됨)" -ForegroundColor DarkGray } catch {}
Write-Host ""
Write-Host "  API Key 는 아무 글자나 (Ollama 가 검사 안 함)"
Write-Host "  다 쓰면 반드시 .\터널-닫기.ps1 로 닫으세요 — 인증이 없는 상태로 열려 있습니다." -ForegroundColor Yellow
