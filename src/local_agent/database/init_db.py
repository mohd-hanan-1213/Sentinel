from .base import Base
from .connection import engine
from . import models


def initialize_database():
    Base.metadata.create_all(bind=engine)
    print("Sentinel database tables created successfully.")


if __name__ == "__main__":
    initialize_database()