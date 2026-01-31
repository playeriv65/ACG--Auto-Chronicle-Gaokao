# Start JieKang School Novel Generation
$script = "main.py"
$stdout = "runtime.log"
$stderr = "error.log"

Write-Host "[INFO] Initializing Background Generation..."

# Start process in background
Start-Process -FilePath "python.exe" -ArgumentList "main.py" -RedirectStandardOutput $stdout -RedirectStandardError $stderr -NoNewWindow

Write-Host "[SUCCESS] Generation is now running in the background."
