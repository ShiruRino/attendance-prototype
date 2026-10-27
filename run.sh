#!/usr/bin/env bash
set -e

# Pindah ke direktori script ini berada
cd "$(dirname "$0")"

echo "=================================================="
echo " Face Attendance MVP (SFace + YuNet) - Linux/macOS"
echo "=================================================="

# 1. Cek Python3
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 tidak ditemukan. Silakan install Python 3.9+ terlebih dahulu."
    exit 1
fi

# 2. Cek & Buat Virtual Environment
if [ ! -d ".venv" ]; then
    echo "[INFO] Membuat virtual environment .venv..."
    python3 -m venv .venv
    echo "[INFO] Menginstall dependencies dari requirements.txt..."
    .venv/bin/pip install --upgrade pip
    .venv/bin/pip install -r requirements.txt
fi

# 3. Cek & Download Model ONNX jika belum ada
mkdir -p models
YUNET_MODEL="models/face_detection_yunet_2023mar.onnx"
SFACE_MODEL="models/face_recognition_sface_2021dec.onnx"

if [ ! -f "$YUNET_MODEL" ]; then
    echo "[INFO] Mengunduh model YuNet (Face Detection)..."
    curl -L -o "$YUNET_MODEL" https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx
fi

if [ ! -f "$SFACE_MODEL" ]; then
    echo "[INFO] Mengunduh model SFace (Face Recognition)..."
    curl -L -o "$SFACE_MODEL" https://github.com/opencv/opencv_zoo/raw/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx
fi

# 4. Jalankan Aplikasi
echo "=================================================="
echo " Server berjalan di: http://localhost:8000        "
echo " Tekan CTRL+C untuk berhenti                     "
echo "=================================================="

source .venv/bin/activate
python app.py
