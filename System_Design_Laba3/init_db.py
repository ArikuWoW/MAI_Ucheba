import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from System_Design_Laba3.main import Base, UserDB, ReportDB, ConferenceDB
from passlib.context import CryptContext

# Настройка PostgreSQL
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:archdb@db/event_boost_db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Настройка паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Создание таблиц
Base.metadata.create_all(bind=engine)

# Загрузка тестовых данных
def load_test_data():
    db = SessionLocal()

    # Проверка существования пользователя перед добавлением
    def add_user(login, first_name, last_name, hashed_password):
        user = db.query(UserDB).filter(UserDB.login == login).first()
        if not user:
            user = UserDB(
                login=login,
                first_name=first_name,
                last_name=last_name,
                hashed_password=hashed_password,
            )
            db.add(user)

    # Создание пользователей
    add_user(
        login="admin",
        first_name="Admin",
        last_name="Admin",
        hashed_password=pwd_context.hash("admin123"),
    )

    add_user(
        login="user1",
        first_name="Gleb",
        last_name="Glebov",
        hashed_password=pwd_context.hash("user123"),
    )



    # Создание докладов
    def add_report(title, author_id, description):
        report = db.query(ReportDB).filter(ReportDB.title == title).first()
        if not report:
            report = ReportDB(
                title=title,
                author_id=author_id,
                description=description,
            )
            db.add(report)


    # Создание конференций
    def add_conference(user_id):
        conference = db.query(ConferenceDB).filter(ConferenceDB.user_id == user_id).first()
        if not conference:
            cart = ConferenceDB(user_id=user_id)
            db.add(conference)

    add_conference(1)  # admin

