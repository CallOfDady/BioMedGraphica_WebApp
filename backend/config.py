# backend/config.py
import os
from pathlib import Path

class Config:
    # Get database path from environment variable or use default
    DATABASE_PATH = os.getenv(
        "BIOMEDGRAPHICA_DB_PATH", 
        "E:/LabWork/BioMedGraphica-Conn"
    )
    
    @classmethod
    def validate_config(cls):
        """Validate configuration at startup"""
        db_path = Path(cls.DATABASE_PATH)
        if not db_path.exists():
            raise ValueError(
                f"Database path does not exist: {cls.DATABASE_PATH}\n"
                f"Please check your configuration or set BIOMEDGRAPHICA_DB_PATH environment variable"
            )
        return True