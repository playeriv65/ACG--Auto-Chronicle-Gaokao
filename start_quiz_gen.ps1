# 后台启动天库大阵
$stdout = "quiz_gen.log"
$stderr = "quiz_gen_error.log"

Write-Host "[INFO] Starting Background Quiz Generation..."

# 确保旧进程已清空
Get-Process | Where-Object {$_.ProcessName -eq "python"} | Stop-Process -Force -ErrorAction SilentlyContinue

# 启动
Start-Process -FilePath "python.exe" -ArgumentList "batch_quiz_gen.py" -RedirectStandardOutput $stdout -RedirectStandardError $stderr -NoNewWindow

Write-Host "[SUCCESS] Great Library Task is running in background."
Write-Host "[INFO] Monitor: Get-Content $stdout -Wait"
