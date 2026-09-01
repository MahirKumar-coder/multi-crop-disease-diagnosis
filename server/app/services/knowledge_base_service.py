import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from app.core.logger import logger

class KnowledgeBaseService:
    _instance = None
    _db: Dict[str, Any] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(KnowledgeBaseService, cls).__new__(cls)
            cls._instance._load_database()
        return cls._instance

    def _load_database(self):
        current_dir = Path(__file__).resolve().parent
        candidates = [
            current_dir / ".." / "data" / "remediation_data.json",
            Path("server/app/data/remediation_data.json"),
            Path("app/data/remediation_data.json"),
            Path("data/remediation_data.json")
        ]
        
        db_path = None
        for c in candidates:
            if c.exists():
                db_path = c.resolve()
                break

        if db_path and os.path.exists(db_path):
            try:
                with open(db_path, "r", encoding="utf-8") as f:
                    self._db = json.load(f)
                logger.info(f"Loaded {len(self._db)} disease records from {db_path}")
            except Exception as e:
                logger.error(f"Failed to load remediation database: {e}")
                self._db = {}
        else:
            logger.warning(f"Remediation database not found in candidate paths.")
            self._db = {}

    def get_disease_details(self, class_id: str) -> Optional[Dict[str, Any]]:
        return self._db.get(class_id, None)

    @property
    def all_records(self) -> Dict[str, Any]:
        return self._db

kb_service = KnowledgeBaseService()
