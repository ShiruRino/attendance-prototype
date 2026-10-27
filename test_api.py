import base64
import os
from starlette.testclient import TestClient
from app import app
import database

def test_api_endpoints():
    with TestClient(app) as client:
        # 1. Test index page
        res = client.get("/")
        assert res.status_code == 200
        assert "Face Attendance MVP" in res.text
        print("GET / -> 200 OK")

        # 2. Read test face image as base64
        with open("test_face.jpg", "rb") as f:
            b64_img = "data:image/jpeg;base64," + base64.b64encode(f.read()).decode("utf-8")

        # 3. Test Register endpoint
        reg_payload = {
            "employee_id": "EMP-8888",
            "name": "Budi Santoso",
            "image": b64_img
        }
        res = client.post("/api/register", json=reg_payload)
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        print("POST /api/register -> 200 OK:", data["message"])

        # 4. Test Recognize endpoint
        rec_payload = {
            "image": b64_img,
            "attendance_type": "CHECK_IN"
        }
        res = client.post("/api/recognize", json=rec_payload)
        assert res.status_code == 200
        data = res.json()
        assert data["detected"] is True
        assert data["recognized"] is True
        assert data["employee_id"].startswith("EMP-")
        assert data["attendance_type"] == "CHECK_IN"
        assert data["similarity"] >= 0.363
        print(f"POST /api/recognize -> 200 OK: Recognized {data['name']} ({data['employee_id']}) with {data['confidence_pct']}% confidence")

        # 5. Test Confirm Attendance endpoint
        confirm_payload = {
            "employee_id": data["employee_id"],
            "name": data["name"],
            "attendance_type": data["attendance_type"],
            "similarity": data["similarity"]
        }
        res = client.post("/api/confirm_attendance", json=confirm_payload)
        assert res.status_code == 200
        conf_data = res.json()
        assert conf_data["success"] is True
        print("POST /api/confirm_attendance -> 200 OK:", conf_data["message"])

        # 6. Test Get Logs
        res = client.get("/api/attendance_logs")
        assert res.status_code == 200
        logs = res.json()["logs"]
        assert len(logs) > 0
        assert logs[0]["employee_id"] == data["employee_id"]
        print("GET /api/attendance_logs -> 200 OK. Total logs:", len(logs))

        # 7. Test Get Users
        res = client.get("/api/users")
        assert res.status_code == 200
        users = res.json()["users"]
        assert any(u["employee_id"] == "EMP-8888" for u in users)
        print("GET /api/users -> 200 OK. Total users:", len(users))

        print("\n🎉 ALL API ENDPOINTS VERIFIED & WORKING PERFECTLY! 🎉")

if __name__ == "__main__":
    test_api_endpoints()
