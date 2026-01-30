@echo off
echo [INFO] Detected Spirit Root... Initializing Cultivation Environment (Virtualenv)...

python -m venv venv
if %errorlevel% neq 0 (
    echo [ERROR] Failed to condense Spirit Qi (Create venv failed).
    pause
    exit /b
)

echo [INFO] Entering the Sect (Activating venv)...
call venv\Scripts\activate

echo [INFO] Refining Artifacts (Installing requirements)...
pip install -r requirements.txt

echo [SUCCESS] Foundation Establishment Complete! You may now run 'python main_v5_pro.py'.
pause
