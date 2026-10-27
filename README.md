# Face Attendance Prototype (MVP)

Prototype aplikasi absensi berbasis pengenalan wajah (*Face Recognition*) menggunakan **OpenCV YuNet** (Face Detection) dan **SFace** (Face Recognition). Dibuat secara ringkas, tanpa *overengineering*, dengan palet minimalis monokrom (*Ink & Greys*) dan satu aksen warna (*Electric Blue*).

---

## 🚀 Fitur Utama

1. **Registrasi Wajah (Face Registration)**
   - Input ID/NIP dan Nama Karyawan.
   - Tangkap foto langsung dari webcam browser atau upload gambar.
   - YuNet mendeteksi wajah dan 5 landmark, lalu SFace mengekstrak embedding 128-dimensi ke SQLite (`attendance.db`).

2. **Absensi Check-In / Check-Out**
   - Toggle pilihan presensi (Check-In / Check-Out).
   - Verifikasi wajah real-time via kamera.
   - Pencocokan Cosine Similarity menggunakan SFace (threshold standar: `0.363`).

3. **Multi-Wajah & Pemilihan Manual**
   - Jika terdeteksi lebih dari 1 orang dalam 1 frame, sistem menyajikan kartu pilihan foto masing-masing orang.
   - Pengguna dapat memilih wajahnya secara manual untuk melakukan konfirmasi absensi.
   - Jika wajah belum terdaftar atau confidencenya kurang, sistem tidak mencatut nama orang lain dan menandainya dengan label **"Diduga"** serta menonaktifkan tombol simpan.

4. **Konfirmasi Data (Attendance Confirmation Modal)**
   - Saat wajah terverifikasi, muncul modal dialog konfirmasi yang menampilkan foto hasil tangkapan, nama, ID, jenis absensi, dan skor kemiripan.
   - Data absensi baru disimpan setelah pengguna menekan tombol **"Ya, Benar"**.

5. **Riwayat Absensi & Karyawan Terdaftar**
   - Log kehadiran real-time dan daftar karyawan dengan opsi hapus.

---

## 🛠️ Struktur Project

```text
attendance-prototype/
├── app.py                     # Server FastAPI & API Endpoints
├── face_engine.py             # Engine YuNet (Detector) & SFace (Recognizer)
├── database.py                # Database SQLite (users & attendance_logs)
├── models/                    # Model ONNX resmi (auto-download jika belum ada)
│   ├── face_detection_yunet_2023mar.onnx
│   └── face_recognition_sface_2021dec.onnx
├── static/
│   └── app.js                 # Frontend webcam, manual selection & modal logic
├── templates/
│   └── index.html             # Tampilan UI modern (Tailwind CSS, Ink & Greys)
├── requirements.txt           # Dependensi Python
├── run.sh                     # 1-Click Runner untuk Linux / macOS
├── run.bat                    # 1-Click Runner untuk Windows
├── .gitignore                 # Filter git (mengabaikan venv, db, cache)
├── test_pipeline.py           # Unit test pipeline OpenCV
├── test_multi_face.py         # Test multi-face selection
└── test_api.py                # End-to-end API test
```

---

## ⚡ Quick Installation & Run

### 🐧 Linux & macOS

#### Cara Cepat (Otomatis):
Cukup jalankan script `run.sh` (script akan otomatis membuat virtual environment, menginstall dependencies, dan mengunduh model ONNX jika belum ada):
```bash
./run.sh
```

#### Cara Manual (Step-by-Step):
```bash
# 1. Buat virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Install dependensi
pip install --upgrade pip
pip install -r requirements.txt

# 3. Jalankan aplikasi
python3 app.py
```

---

### 🪟 Windows

#### Cara Cepat (Otomatis):
Klik dua kali file **`run.bat`**, atau jalankan lewat Command Prompt / PowerShell:
```cmd
run.bat
```
*(Script akan otomatis mengecek Python, membuat `.venv`, menginstall dependensi, mendownload model jika belum ada, dan menjalankan server)*.

#### Cara Manual (Step-by-Step):
Buka PowerShell atau Command Prompt di folder project:
```powershell
# 1. Buat virtual environment
python -m venv .venv
.\.venv\Scripts\activate

# 2. Install dependensi
python -m pip install --upgrade pip
pip install -r requirements.txt

# 3. Jalankan aplikasi
python app.py
```

---

## 🌐 Membuka Aplikasi

Setelah server berjalan, buka browser dan akses:
```text
http://localhost:8000
```
> **Catatan Kamera**: Pastikan Anda mengizinkan (*Allow*) akses webcam pada browser saat halaman pertama kali dibuka. Jika tidak memiliki webcam, Anda dapat menggunakan tombol **"Upload Foto"** yang tersedia di aplikasi.

---

## 🧪 Menjalankan Pengujian Otomatis

Untuk memverifikasi bahwa model OpenCV, deteksi multi-wajah, dan endpoint API berfungsi dengan baik:

```bash
# Linux / macOS
.venv/bin/python test_pipeline.py
.venv/bin/python test_multi_face.py
.venv/bin/python test_api.py

# Windows
.\.venv\Scripts\python test_pipeline.py
.\.venv\Scripts\python test_multi_face.py
.\.venv\Scripts\python test_api.py
```

---

## 📦 Push ke GitHub

File [`.gitignore`](.gitignore) sudah disiapkan untuk mengecualikan file lokal seperti `.venv/`, database lokal `attendance.db`, dan cache `__pycache__/`.

Langkah push ke repository GitHub baru:
```bash
git add .
git commit -m "feat: face attendance mvp with sface, yunet, and ink-grey gui"
git branch -M main
git remote add origin https://github.com/USERNAME/REPO_NAME.git
git push -u origin main
```
