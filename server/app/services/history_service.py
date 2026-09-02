import os
import sqlite3
from datetime import datetime, timezone
from typing import List, Dict, Any
from app.core.logger import logger

DB_FILE_PATH = os.path.join(os.path.dirname(__file__), "../data/diagnostics_history.db")

class DiagnosticHistoryService:
    def __init__(self, db_path: str = DB_FILE_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Initializes the diagnostic audit logs table."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS diagnostic_audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    crop TEXT NOT NULL,
                    disease_name TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    is_confident INTEGER NOT NULL,
                    status_flag TEXT NOT NULL,
                    latency_ms REAL NOT NULL,
                    client_ip TEXT
                )
            """)
            conn.commit()
        logger.info(f"Initialized diagnostic audit database at: {self.db_path}")

    def log_diagnosis(
        self,
        crop: str,
        disease_name: str,
        confidence: float,
        is_confident: bool,
        status_flag: str,
        latency_ms: float,
        client_ip: str = "127.0.0.1"
    ) -> int:
        """Inserts a single scan record into the audit log."""
        iso_timestamp = datetime.now(timezone.utc).isoformat()
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO diagnostic_audit_logs 
                    (timestamp, crop, disease_name, confidence, is_confident, status_flag, latency_ms, client_ip)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    iso_timestamp,
                    crop,
                    disease_name,
                    round(confidence, 2),
                    1 if is_confident else 0,
                    status_flag,
                    round(latency_ms, 2),
                    client_ip
                ))
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Failed to record diagnostic audit log: {str(e)}")
            return -1

    def get_records(self, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """Retrieves recent scan records ordered by latest timestamp."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM diagnostic_audit_logs")
            total = cursor.fetchone()[0]

            cursor.execute("""
                SELECT id, timestamp, crop, disease_name, confidence, 
                       is_confident, status_flag, latency_ms, client_ip
                FROM diagnostic_audit_logs
                ORDER BY id DESC
                LIMIT ? OFFSET ?
            """, (limit, offset))
            rows = cursor.fetchall()

            records = [
                {
                    "id": row["id"],
                    "timestamp": row["timestamp"],
                    "crop": row["crop"],
                    "disease_name": row["disease_name"],
                    "confidence": row["confidence"],
                    "is_confident": bool(row["is_confident"]),
                    "status_flag": row["status_flag"],
                    "latency_ms": row["latency_ms"],
                    "client_ip": row["client_ip"]
                }
                for row in rows
            ]

        return {"total_records": total, "records": records}

    def clear_records(self) -> int:
        """Truncates the audit log table."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM diagnostic_audit_logs")
            count = cursor.fetchone()[0]
            cursor.execute("DELETE FROM diagnostic_audit_logs")
            conn.commit()
        logger.info(f"Cleared {count} diagnostic audit records.")
        return count

# Singleton instance
history_service = DiagnosticHistoryService()