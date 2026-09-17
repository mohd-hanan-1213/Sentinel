from src.local_agent.database.base import Base
from src.local_agent.database.connection import engine
from src.local_agent.database import models


def init_database():
    Base.metadata.create_all(bind=engine)
    print("Sentinel database tables created successfully.")


if __name__ == "__main__":
    init_database()