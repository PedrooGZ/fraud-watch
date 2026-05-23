from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from src.db.base import Base
from src.db.models import ModelVersion, Policy, User
from src.db.session import SessionLocal, engine


def seed_defaults() -> None:
    with SessionLocal() as session:
        existing_user = session.scalar(select(User).where(User.email == "admin@fraudwatch.local"))
        if existing_user is None:
            session.add(
                User(
                    email="admin@fraudwatch.local",
                    full_name="Admin Fraud Watch",
                    role="admin",
                    password_hash=None,
                    is_active=True,
                )
            )

        existing_model = session.scalar(
            select(ModelVersion).where(
                ModelVersion.name == "fraud_model",
                ModelVersion.is_active.is_(True),
            )
        )
        if existing_model is None:
            session.add(
                ModelVersion(
                    name="fraud_model",
                    model_type="HistGradientBoosting + Isotonic",
                    artifact_path="artifacts/fraud_model.joblib",
                    metadata_path="artifacts/fraud_model_metadata.json",
                    pr_auc=0.797619,
                    brier_score=0.000608,
                    n_features=29,
                    is_active=True,
                )
            )

        existing_policy = session.scalar(select(Policy).where(Policy.is_active.is_(True)))
        if existing_policy is None:
            session.add(
                Policy(
                    threshold_cost=0.02,
                    max_alerts=500,
                    priority_mode="risk",
                    error_cost_mode="balanced",
                    is_active=True,
                )
            )

        session.commit()


def main() -> None:
    try:
        Base.metadata.create_all(bind=engine)
        seed_defaults()
        print("Base de datos inicializada correctamente.")
    except SQLAlchemyError as exc:
        print(f"Error al inicializar base de datos: {exc}")
        raise


if __name__ == "__main__":
    main()
