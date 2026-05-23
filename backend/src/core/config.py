from pathlib import Path
import os

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BACKEND_DIR / ".env")

DATA_DIR = BACKEND_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
SCORES_DIR = DATA_DIR / "scores"

ARTIFACTS_DIR = BACKEND_DIR / "artifacts"
DOCS_DIR = BACKEND_DIR / "docs"
LOGS_DIR = BACKEND_DIR / "logs"

MODEL_PATH = ARTIFACTS_DIR / "fraud_model.joblib"
MODEL_METADATA_PATH = ARTIFACTS_DIR / "fraud_model_metadata.json"
REVIEW_POLICY_PATH = BACKEND_DIR / "review_policy.json"
PREDICTIONS_LOG_PATH = LOGS_DIR / "predictions.jsonl"

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://fraud_user:fraud_password@localhost:5432/fraud_watch",
)

JWT_SECRET_KEY = os.getenv(
    "JWT_SECRET_KEY",
    "fraud-watch-dev-secret-key-change-me-2026-minimum-32-bytes",
)
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
