import cv2
import numpy as np
import database
from face_engine import FaceEngine

def test_multiple_faces_recognition():
    print("=== Testing Multiple Faces in Frame ===")
    database.init_db()
    engine = FaceEngine()

    # Load test face image
    img = cv2.imread("test_face.jpg")
    h, w = img.shape[:2]

    # Create composite image with 2 faces:
    # Face A: Left side (Registered User)
    # Face B: Right side (Friend / Unregistered)
    composite = np.zeros((h, w * 2, 3), dtype=np.uint8)
    composite[:, :w] = img
    composite[:, w:] = cv2.flip(img, 1) # flipped face on right side

    # Extract single face feature to register
    res = engine.process_and_extract(img)
    emp_id = "EMP-MULTI-001"
    name = "Karyawan Utama"
    database.save_user(emp_id, name, res["feature"])

    registered_users = database.get_all_users()

    # Run recognition on multi-face frame
    rec_res = engine.recognize_all_candidates(composite, registered_users)
    print("Recognition Result on 2 faces in frame:")
    print(f"Detected: {rec_res['detected']}")
    print(f"Faces Count: {rec_res['faces_count']}")
    print(f"Total Candidates: {len(rec_res['candidates'])}")
    for i, c in enumerate(rec_res['candidates']):
        print(f"  Candidate {i}: Name={c['name']}, Recognized={c['recognized']}, Similarity={c['similarity']}")

    assert rec_res["detected"] is True
    assert rec_res["faces_count"] >= 2, "Should detect at least 2 faces"
    assert any(c["employee_id"] == emp_id for c in rec_res["candidates"]), "Registered user should be in candidates"

    print("\n✅ MULTI-FACE AUTOMATIC SELECTION TEST PASSED! ✅")

if __name__ == "__main__":
    test_multiple_faces_recognition()

