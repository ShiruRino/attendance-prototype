@echo off
setlocal enabledelayedexpansion

echo ==================================================
echo  Face Attendance MVP (SFace + YuNet) - Windows
echo ==================================================

:: 1. Cek Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python tidak ditemukan di PATH.
    echo Silakan install Python dari python.org dan centang "Add Python to PATH".
    pause
    exit /b 1
)

:: 2. Cek & Buat Virtual Environment
if not exist ".venv" (
    echo [INFO] Membuat virtual environment .venv...
    python -m venv .venv
    echo [INFO] Menginstall dependencies dari requirements.txt...
    call .venv\Scripts\activate.bat
    python -m pip install --upgrade pip
    pip install -r requirements.txt
) else (
    call .venv\Scripts\activate.bat
)

:: 3. Cek & Download Model ONNX jika belum ada
if not exist "models" mkdir models

set YUNET_MODEL=models\face_detection_yunet_2023mar.onnx
set SFACE_MODEL=models\face_recognition_sface_2021dec.onnx

if not exist "%YUNET_MODEL%" (
    echo [INFO] Mengunduh model YuNet (Face Detection)...
    powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; (New-Object System.Net.WebClient).DownloadFile('https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx', '%YUNET_MODEL%')"
)

if not exist "%SFACE_MODEL%" (
    echo [INFO] Mengunduh model SFace (Face Recognition)...
    powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; (New-Object System.Net.WebClient).DownloadFile('https://github.com/opencv/opencv_zoo/raw/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx', '%SFACE_MODEL%')"
)

:: 4. Jalankan Aplikasi
echo ==================================================
echo  Server berjalan di: http://localhost:8000
echo  Buka browser Anda di URL tersebut.
echo  Tekan CTRL+C di jendela ini untuk berhenti.
echo ==================================================

python app.py

pause

