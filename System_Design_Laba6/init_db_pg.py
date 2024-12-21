import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from event_boost import Base, ReportDB, ConferenceDB, ConferenceReportDB

SQLALCHEMY_DATABASE_URL = "postgresql://postgres:secret@db:5432/conference_db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def load_test_data():
    db = SessionLocal()
    def add_report(title, content, author_id):
        report = ReportDB(title=title, content=content, author_id=author_id)
        db.add(report)

    def add_conference(name):
        conference = ConferenceDB(name=name)
        db.add(conference)

    add_report("Доклад 1", "Содержание доклада 1", 1)
    add_conference("Конференция 1")

    db.commit()
    db.close()

def wait_for_db(retries=10, delay=5):
    for _ in range(retries):
        try:
            engine.connect()
            print("PostgreSQL is ready!")
            return
        except Exception as e:
            print(f"Waiting for PostgreSQL: {e}")
            time.sleep(delay)
    raise Exception("Could not connect to PostgreSQL")

if __name__ == "__main__":
    wait_for_db()
    Base.metadata.create_all(bind=engine)
    load_test_data()
