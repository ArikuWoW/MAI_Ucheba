import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from event_boost import Base, UserDB, ReportDB, ConferenceDB

# Настройка PostgreSQL
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:secret@db:5432/conference_db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Создание таблиц
Base.metadata.create_all(bind=engine)

# Загрузка тестовых данных
def load_test_data():
    db = SessionLocal()

    # Проверка существования и добавление пользователя
    def add_user(username, email, hashed_password):
        try:
            user = UserDB(username=username, email=email, hashed_password=hashed_password)
            db.add(user)
            db.commit()
        except IntegrityError:
            db.rollback()  # Пропуск, если пользователь уже существует

    # Проверка существования и добавление доклада
    def add_report(title, content, author_id):
        try:
            report = ReportDB(title=title, content=content, author_id=author_id)
            db.add(report)
            db.commit()
        except IntegrityError:
            db.rollback()  # Пропуск, если доклад уже существует

    # Проверка существования и добавление конференции
    def add_conference(name):
        try:
            conference = ConferenceDB(name=name)
            db.add(conference)
            db.commit()
        except IntegrityError:
            db.rollback()  # Пропуск, если конференция уже существует

    # Добавление тестовых данных
    add_user(username="admin", email="admin@example.com", hashed_password="hashed_password_admin")
    add_user(username="user1", email="user1@example.com", hashed_password="hashed_password_user1")
    add_user(username="user2", email="user2@example.com", hashed_password="hashed_password_user2")

    add_report(title="Доклад 1", content="Содержание доклада 1", author_id=1)
    add_report(title="Доклад 2", content="Содержание доклада 2", author_id=2)

    add_conference(name="Конференция 1")
    add_conference(name="Конференция 2")

    db.close()

def wait_for_db(retries=10, delay=5):
    for _ in range(retries):
        try:
            engine.connect()
            print("PostgreSQL is ready!")
            return
        except Exception as e:
            print(f"PostgreSQL not ready yet: {e}")
            time.sleep(delay)
    raise Exception("Could not connect to PostgreSQL")

if __name__ == "__main__":
    wait_for_db()
    load_test_data()
