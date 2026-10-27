import os
import cv2
import base64
import numpy as np
import database
from face_engine import FaceEngine

def test_full_flow():
    print("=== Testing Database Init ===")
    database.init_db()

    print("=== Testing FaceEngine Init ===")
    engine = FaceEngine()

    print("=== Testing Face Detection on test_face.jpg ===")
    img = cv2.imread("test_face.jpg")
    assert img is not None, "Failed to load test image"
    
    res = engine.process_and_extract(img)
    print(f"Detection Success: {res['success']}, Fallback Used: {res['fallback_used']}, Face Box: {res['face_box']}")
    assert res["success"], "Face should be detected in test_face.jpg"
    assert res["feature"] is not None
    assert res["feature"].shape == (1, 128)

    print("=== Testing User Registration in DB ===")
    emp_id = "EMP-TEST-001"
    name = "Test Karyawan"
    database.save_user(emp_id, name, res["feature"])

    users = database.get_all_users()
    print(f"Total Users Registered: {len(users)}")
    assert any(u["employee_id"] == emp_id for u in users)

    print("=== Testing Face Recognition (Self Match) ===")
    match_res = engine.match_face(res["feature"], users)
    print(f"Match Recognized: {match_res['recognized']}, Similarity: {match_res['similarity']:.4f}, Threshold: {match_res['threshold']}")
    assert match_res["recognized"], "Self match should exceed threshold"
    assert match_res["user"]["employee_id"] == emp_id

    print("=== Testing Attendance Logging & Confirmation ===")
    rec = database.save_attendance(emp_id, name, "CHECK_IN", match_res["similarity"])
    print(f"Saved Attendance Record: {rec}")
    assert rec["employee_id"] == emp_id
    assert rec["attendance_type"] == "CHECK_IN"

    logs = database.get_attendance_logs(5)
    print(f"Total Logs: {len(logs)}")
    assert len(logs) > 0
    assert logs[0]["employee_id"] == emp_id

    print("\n✅ ALL TESTS PASSED SUCCESSFULLY! ✅")

if __name__ == "__main__":
    test_full_flow()

