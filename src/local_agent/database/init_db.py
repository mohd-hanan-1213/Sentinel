from src.local_agent.database.base import Base
from src.local_agent.database.connection import engine
from src.local_agent.database import models
from sqlalchemy import text


def init_database():
    Base.metadata.create_all(bind=engine)
    _apply_schema_upgrades()
    print("Sentinel database tables created successfully.")


def _apply_schema_upgrades():
    """Apply safe additive upgrades for databases created by earlier versions."""
    with engine.begin() as connection:
        connection.execute(text(
            "ALTER TABLE evidence "
            "ADD COLUMN IF NOT EXISTS expires_at TIMESTAMP "
            "NOT NULL DEFAULT CURRENT_TIMESTAMP"
        ))


if __name__ == "__main__":
    init_database()
