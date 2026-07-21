from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

SQLITE_URL = "sqlite:///./bank.db"

engine = create_engine(
    SQLITE_URL, connect_args={"check_same_thread": False}, future=True
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.close()
