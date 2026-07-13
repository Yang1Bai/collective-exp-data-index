@echo off
REM One-command campaign runner (for OpenClaw command payloads / Task Scheduler).
REM Usage: run_campaign.cmd [smoke|flagship|full]   (default: smoke)
REM Activates Anaconda base (fixes the SSL DLL issue), runs the stage, logs everything.
setlocal
set STAGE=%1
if "%STAGE%"=="" set STAGE=smoke

call "D:\Program\anaconda3\Scripts\activate.bat" "D:\Program\anaconda3"
cd /d "%~dp0"

echo ============================================== >> campaign.log
echo [%date% %time%] START stage=%STAGE% >> campaign.log

if "%STAGE%"=="smoke" (
    python nature_campaign.py run --topic "perovskite solar cell" --max 10 >> campaign.log 2>&1
) else if "%STAGE%"=="flagship" (
    python nature_campaign.py hybrid --journal "Nature Materials" --max-per-journal 100 >> campaign.log 2>&1
) else if "%STAGE%"=="full" (
    python nature_campaign.py preset --max-per-query 15 >> campaign.log 2>&1
    python nature_campaign.py hybrid --max-per-journal 200 >> campaign.log 2>&1
) else (
    echo unknown stage %STAGE% >> campaign.log
    exit /b 2
)

echo [%date% %time%] END stage=%STAGE% exitcode=%errorlevel% >> campaign.log
echo Latest candidate files: >> campaign.log
dir /b /o-d "..\discovered\nature_*.json" 2>nul | findstr /n "^" | findstr "^[1-3]:" >> campaign.log
endlocal
