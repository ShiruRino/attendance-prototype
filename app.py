import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
import uvicorn

import database
from face_engine import FaceEngine

# Inisialisasi FaceEngine & Database
face_engine = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global face_engine
    database.init_db()
    face_engine = FaceEngine()
    print(">>> Face Recognition Attendance System Ready <<<")
    yield

app = FastAPI(title="Face Attendance Prototype", lifespan=lifespan)

# Setup static and templates
os.makedirs("static", exist_ok=True)
os.makedirs("templates", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Pydantic Schemas
class RegisterRequest(BaseModel):
    employee_id: str = Field(..., description="ID / NIK Karyawan")
    name: str = Field(..., description="Nama Lengkap Karyawan")
    image: str = Field(..., description="Base64 encoded snapshot wajah")

class RecognizeRequest(BaseModel):
    image: str = Field(..., description="Base64 encoded snapshot wajah")
    attendance_type: str = Field(default="CHECK_IN", description="CHECK_IN atau CHECK_OUT")

class AttendanceConfirmRequest(BaseModel):
    employee_id: str
    name: str
    attendance_type: str
    similarity: float

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@app.post("/api/register")
async def register_user(payload: RegisterRequest):
    if not payload.employee_id.strip() or not payload.name.strip():
        raise HTTPException(status_code=400, detail="ID Karyawan dan Nama tidak boleh kosong.")
    
    try:
        img_bgr = face_engine.decode_image(payload.image)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Gagal memproses gambar: {str(e)}")

    # Ekstraksi fitur wajah (YuNet detector -> SFace embedding)
    res = face_engine.process_and_extract(img_bgr)
    if not res["success"]:
        return JSONResponse(status_code=400, content={
            "success": False,
            "message": res["message"],
            "fallback_used": res["fallback_used"]
        })

    # Simpan ke database
    database.save_user(payload.employee_id, payload.name, res["feature"])
    
    return {
        "success": True,
        "message": f"Wajah {payload.name} ({payload.employee_id}) berhasil didaftarkan!",
        "face_box": res["face_box"],
        "fallback_used": res["fallback_used"]
    }

@app.post("/api/recognize")
async def recognize_face(payload: RecognizeRequest):
    try:
        img_bgr = face_engine.decode_image(payload.image)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Gagal memproses gambar: {str(e)}")

    registered_users = database.get_all_users()
    rec_res = face_engine.recognize_all_candidates(img_bgr, registered_users)

    if not rec_res["detected"] or len(rec_res["candidates"]) == 0:
        return {
            "detected": False,
            "recognized": False,
            "candidates": [],
            "faces_count": 0,
            "message": rec_res["message"],
            "fallback_used": False
        }

    candidates = rec_res["candidates"]
    # Pilihan default awal: utamakan kandidat yang terdaftar, atau indeks 0
    recognized_candidates = [c for c in candidates if c["recognized"]]
    default_candidate = recognized_candidates[0] if recognized_candidates else candidates[0]

    return {
        "detected": True,
        "faces_count": len(candidates),
        "candidates": candidates,
        "fallback_used": rec_res["fallback_used"],
        "attendance_type": payload.attendance_type.upper(),
        # Default candidate fields:
        "recognized": default_candidate["recognized"],
        "employee_id": default_candidate["employee_id"],
        "name": default_candidate["name"],
        "similarity": default_candidate["similarity"],
        "confidence_pct": default_candidate["confidence_pct"],
        "crop_image": default_candidate["crop_image"],
        "message": f"Terdeteksi {len(candidates)} wajah di kamera."
    }

@app.post("/api/confirm_attendance")
async def confirm_attendance(payload: AttendanceConfirmRequest):
    record = database.save_attendance(
        employee_id=payload.employee_id,
        name=payload.name,
        attendance_type=payload.attendance_type.upper(),
        similarity=payload.similarity
    )
    return {
        "success": True,
        "message": f"Absensi {payload.attendance_type.upper()} berhasil dicatat untuk {payload.name}.",
        "record": record
    }

@app.get("/api/attendance_logs")
async def get_logs():
    logs = database.get_attendance_logs(limit=50)
    return {"logs": logs}

@app.get("/api/users")
async def get_users():
    users = database.get_users_list()
    return {"users": users, "count": len(users)}

@app.delete("/api/users/{employee_id}")
async def delete_user(employee_id: str):
    database.delete_user(employee_id)
    return {"success": True, "message": f"User {employee_id} berhasil dihapus."}

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
