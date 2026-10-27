import cv2
import numpy as np
import base64
import os
from typing import Tuple, Optional, List, Dict, Any

YUNET_MODEL_PATH = "models/face_detection_yunet_2023mar.onnx"
SFACE_MODEL_PATH = "models/face_recognition_sface_2021dec.onnx"

# Standar threshold SFace OpenCV untuk Cosine Similarity
# Nilai >= 0.363 dianggap sebagai orang yang sama
COSINE_SIMILARITY_THRESHOLD = 0.363

class FaceEngine:
    def __init__(self):
        if not os.path.exists(YUNET_MODEL_PATH):
            raise FileNotFoundError(f"Model YuNet tidak ditemukan di {YUNET_MODEL_PATH}")
        if not os.path.exists(SFACE_MODEL_PATH):
            raise FileNotFoundError(f"Model SFace tidak ditemukan di {SFACE_MODEL_PATH}")

        # Inisialisasi YuNet Detector
        self.detector = cv2.FaceDetectorYN.create(
            model=YUNET_MODEL_PATH,
            config="",
            input_size=(320, 320),
            score_threshold=0.8,
            nms_threshold=0.3,
            top_k=5000
        )

        # Inisialisasi SFace Recognizer
        self.recognizer = cv2.FaceRecognizerSF.create(
            model=SFACE_MODEL_PATH,
            config=""
        )

    def decode_image(self, image_data: str) -> np.ndarray:
        """Decode base64 string atau data-url menjadi format BGR numpy array."""
        if "," in image_data:
            image_data = image_data.split(",")[1]
        img_bytes = base64.b64decode(image_data)
        nparr = np.frombuffer(img_bytes, np.uint8)
        img_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img_bgr is None:
            raise ValueError("Gagal memproses gambar. Format gambar tidak valid.")
        return img_bgr

    def crop_face_thumbnail(self, img_bgr: np.ndarray, face: np.ndarray) -> str:
        """Crop area wajah dengan padding dan encode ke base64 data-url."""
        h_img, w_img = img_bgr.shape[:2]
        fx, fy, fw, fh = map(int, face[:4])

        pad_x = int(fw * 0.15)
        pad_y = int(fh * 0.15)

        x1 = max(0, fx - pad_x)
        y1 = max(0, fy - pad_y)
        x2 = min(w_img, fx + fw + pad_x)
        y2 = min(h_img, fy + fh + pad_y)

        crop = img_bgr[y1:y2, x1:x2]
        if crop.size == 0:
            crop = img_bgr[fy:fy+fh, fx:fx+fw]

        if crop.shape[0] > 200 or crop.shape[1] > 200:
            crop = cv2.resize(crop, (160, 160), interpolation=cv2.INTER_AREA)

        _, buf = cv2.imencode(".jpg", crop, [cv2.IMWRITE_JPEG_QUALITY, 85])
        b64 = base64.b64encode(buf).decode("utf-8")
        return f"data:image/jpeg;base64,{b64}"

    def detect_faces(self, img_bgr: np.ndarray) -> Tuple[List[np.ndarray], bool]:
        """
        Deteksi wajah menggunakan YuNet.
        Fallback: Jika threshold default (0.8) tidak menemukan wajah,
        secara otomatis fallback ke threshold 0.4.
        """
        h, w = img_bgr.shape[:2]
        self.detector.setInputSize((w, h))

        # 1. Deteksi utama (threshold 0.8)
        self.detector.setScoreThreshold(0.8)
        _, faces = self.detector.detect(img_bgr)
        fallback_used = False

        # 2. Deteksi fallback jika tidak ada wajah
        if faces is None or len(faces) == 0:
            self.detector.setScoreThreshold(0.4)
            _, faces = self.detector.detect(img_bgr)
            if faces is not None and len(faces) > 0:
                fallback_used = True

        if faces is None or len(faces) == 0:
            return [], False

        # Urutkan wajah dari kiri ke kanan (posisi x)
        sorted_faces = sorted(faces, key=lambda f: f[0])
        return sorted_faces, fallback_used

    def extract_feature(self, img_bgr: np.ndarray, face: np.ndarray) -> np.ndarray:
        aligned_face = self.recognizer.alignCrop(img_bgr, face)
        feature = self.recognizer.feature(aligned_face)
        return feature

    def process_and_extract(self, img_bgr: np.ndarray) -> Dict[str, Any]:
        """Ekstrak fitur dari wajah utama (dipakai saat registrasi wajah)."""
        sorted_faces, fallback_used = self.detect_faces(img_bgr)
        if not sorted_faces:
            return {
                "success": False,
                "message": "Wajah tidak terdeteksi. Posisikan wajah di hadapan kamera.",
                "feature": None,
                "face_box": None,
                "fallback_used": False,
                "faces_count": 0
            }

        # Pilih wajah terbesar untuk registrasi
        best_face = max(sorted_faces, key=lambda f: f[2] * f[3])
        feature = self.extract_feature(img_bgr, best_face)
        x, y, w, h = map(int, best_face[:4])
        score = float(best_face[-1])

        return {
            "success": True,
            "message": "Wajah berhasil dideteksi.",
            "feature": feature,
            "face_box": {"x": x, "y": y, "w": w, "h": h, "confidence": round(score, 3)},
            "fallback_used": fallback_used,
            "faces_count": len(sorted_faces)
        }

    def match_face(self, target_feature: np.ndarray, registered_users: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Mencocokkan feature wajah target terhadap user di database.
        Aturan Penting:
        - Jika similarity >= threshold (>= 0.363): Terverifikasi sebagai user tersebut.
        - Jika similarity < threshold: TIDAK BOLEH mencatut nama orang tersebut secara resmi.
          Tandai sebagai 'is_suspected = True' dan cantumkan 'Diduga [Nama]' dengan kemiripan rendah.
        """
        if not registered_users:
            return {
                "recognized": False,
                "user": None,
                "is_suspected": False,
                "suspected_name": None,
                "similarity": 0.0,
                "threshold": COSINE_SIMILARITY_THRESHOLD,
                "message": "Belum ada user yang terdaftar di database."
            }

        best_score = -1.0
        matched_user = None

        for user in registered_users:
            score = self.recognizer.match(target_feature, user["feature"], cv2.FaceRecognizerSF_FR_COSINE)
            if score > best_score:
                best_score = float(score)
                matched_user = user

        is_match = best_score >= COSINE_SIMILARITY_THRESHOLD

        if is_match and matched_user:
            return {
                "recognized": True,
                "is_suspected": False,
                "suspected_name": None,
                "user": {
                    "employee_id": matched_user["employee_id"],
                    "name": matched_user["name"],
                },
                "similarity": best_score,
                "threshold": COSINE_SIMILARITY_THRESHOLD,
                "message": f"Wajah terverifikasi sebagai {matched_user['name']}"
            }
        else:
            # Di bawah threshold: jangan gunakan nama orang sebagai identitas resmi, gunakan 'Diduga'
            suspected_name = matched_user["name"] if (matched_user and best_score >= 0.15) else None
            return {
                "recognized": False,
                "is_suspected": suspected_name is not None,
                "suspected_name": suspected_name,
                "user": None,  # User resmi adalah None karena belum terdaftar
                "similarity": best_score,
                "threshold": COSINE_SIMILARITY_THRESHOLD,
                "message": f"Wajah belum terdaftar (diduga mirip {suspected_name})" if suspected_name else "Wajah belum terdaftar di sistem"
            }

    def recognize_all_candidates(self, img_bgr: np.ndarray, registered_users: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Deteksi semua wajah dalam frame dan lakukan pengenalan SFace untuk masing-masing wajah.
        Menghasilkan list candidates (disertai foto crop thumbnail) sehingga pengguna
        bisa MEMILIH SECARA MANUAL wajah mana yang akan diabsenkan.
        """
        sorted_faces, fallback_used = self.detect_faces(img_bgr)
        if not sorted_faces:
            return {
                "detected": False,
                "candidates": [],
                "fallback_used": False,
                "faces_count": 0,
                "message": "Wajah tidak terdeteksi oleh YuNet. Pastikan menghadap kamera."
            }

        candidates = []
        for idx, face in enumerate(sorted_faces):
            feat = self.extract_feature(img_bgr, face)
            match_res = self.match_face(feat, registered_users)
            crop_thumb = self.crop_face_thumbnail(img_bgr, face)

            fx, fy, fw, fh = map(int, face[:4])
            sim = max(0.0, float(match_res["similarity"]))
            conf_pct = min(100.0, round(sim * 100, 1))

            is_recognized = match_res["recognized"]
            is_suspected = match_res["is_suspected"]
            suspected_name = match_res["suspected_name"]

            if is_recognized and match_res["user"]:
                display_name = match_res["user"]["name"]
                display_id = match_res["user"]["employee_id"]
            elif is_suspected:
                # Confidencenya kurang: jangan pakai nama resmi, tandai belum terdaftar + diduga
                display_name = "Belum Terdaftar"
                display_id = None
            else:
                display_name = "Belum Terdaftar"
                display_id = None

            candidates.append({
                "face_index": idx,
                "crop_image": crop_thumb,
                "recognized": is_recognized,
                "is_suspected": is_suspected,
                "suspected_name": suspected_name,
                "employee_id": display_id,
                "name": display_name,
                "similarity": round(sim, 4),
                "confidence_pct": conf_pct,
                "face_box": {"x": fx, "y": fy, "w": fw, "h": fh, "confidence": round(float(face[-1]), 3)},
                "message": match_res["message"]
            })

        return {
            "detected": True,
            "candidates": candidates,
            "faces_count": len(candidates),
            "fallback_used": fallback_used,
            "message": f"Terdeteksi {len(candidates)} wajah di kamera."
        }
