# Простой тест для проверки, что сервис отвечает.

$base = "http://127.0.0.1:8000"

try {
    $resp = Invoke-RestMethod -Uri "$base/health" -Method Get -ErrorAction Stop
    Write-Host "Health response:" ($resp | ConvertTo-Json -Depth 5)
} catch {
    Write-Host "Не удалось получить /health. Убедитесь, что сервер запущен на $base"
    Write-Host $_.Exception.Message
    exit 1
}

#  получить список тикетов
try {
    $tickets = Invoke-RestMethod -Uri "$base/tickets/" -Method Get -ErrorAction Stop
    Write-Host "Tickets count:" ($tickets.Count)
} catch {
    Write-Host "Ошибка при запросе /tickets/"
    Write-Host $_.Exception.Message
    exit 1
}
