import sqlite3
import os
from typing import List, Optional, Tuple
import numpy as np

DB_FILE = "attendance.db"

def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Tabel data user & face embedding (128 float32 vector)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        feature BLOB NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Tabel log riwayat absensi
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS attendance_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id TEXT NOT NULL,
        name TEXT NOT NULL,
        attendance_type TEXT NOT NULL,
        similarity REAL NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    conn.commit()
    conn.close()

def save_user(employee_id: str, name: str, feature: np.ndarray) -> bool:
    """Simpan atau update user beserta embedding wajahnya."""
    conn = get_connection()
    cursor = conn.cursor()
    feature_blob = feature.astype(np.float32).tobytes()
    
    cursor.execute("""
    INSERT INTO users (employee_id, name, feature, created_at)
    VALUES (?, ?, ?, datetime('now', 'localtime'))
    ON CONFLICT(employee_id) DO UPDATE SET
        name = excluded.name,
        feature = excluded.feature,
        created_at = datetime('now', 'localtime')
    """, (employee_id.strip(), name.strip(), feature_blob))
    
    conn.commit()
    conn.close()
    return True

def get_all_users() -> List[dict]:
    """Ambil semua user dan ubah BLOB kembali ke np.ndarray."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT employee_id, name, feature, created_at FROM users")
    rows = cursor.fetchall()
    conn.close()
    
    users = []
    for r in rows:
        feat = np.frombuffer(r["feature"], dtype=np.float32).reshape(1, 128)
        users.append({
            "employee_id": r["employee_id"],
            "name": r["name"],
            "feature": feat,
            "created_at": r["created_at"]
        })
    return users

def get_users_list() -> List[dict]:
    """Ambil daftar user tanpa blob feature untuk display table."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, employee_id, name, created_at FROM users ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def delete_user(employee_id: str) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE employee_id = ?", (employee_id,))
    conn.commit()
    conn.close()
    return True

def save_attendance(employee_id: str, name: str, attendance_type: str, similarity: float) -> dict:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO attendance_logs (employee_id, name, attendance_type, similarity, timestamp)
    VALUES (?, ?, ?, ?, datetime('now', 'localtime'))
    """, (employee_id, name, attendance_type, round(similarity, 4)))
    
    log_id = cursor.lastrowid
    conn.commit()
    
    cursor.execute("SELECT * FROM attendance_logs WHERE id = ?", (log_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row)

def get_attendance_logs(limit: int = 50) -> List[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT id, employee_id, name, attendance_type, similarity, timestamp 
    FROM attendance_logs 
    ORDER BY id DESC LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

