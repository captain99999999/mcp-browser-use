$conn = Get-NetTCPConnection -LocalPort 8383 -ErrorAction SilentlyContinue
if ($conn) {
    $conn | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }
    Write-Host "Killed process on port 8383"
} else {
    Write-Host "No process on port 8383"
}
