# 터널 닫기 — 내 Ollama 를 인터넷에서 내린다
# 쓰는 법: 파워셸에서  .\터널-닫기.ps1

$p = Get-Process cloudflared -ErrorAction SilentlyContinue
if ($p) {
  $p | Stop-Process -Force
  Start-Sleep -Seconds 1
  Write-Host "  터널 닫음 (프로세스 $($p.Count)개 종료)" -ForegroundColor Green
} else {
  Write-Host "  이미 닫혀 있습니다." -ForegroundColor DarkGray
}

# 확인 — Ollama 는 로컬에서 계속 살아 있어야 정상
try {
  Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -TimeoutSec 5 | Out-Null
  Write-Host "  Ollama 는 로컬에서 정상 (밖에서만 안 보이게 됨)" -ForegroundColor Green
} catch {
  Write-Host "  ! Ollama 가 안 떠 있습니다 (터널과 무관)" -ForegroundColor Yellow
}
