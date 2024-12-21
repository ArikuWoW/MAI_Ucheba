from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from pymongo import MongoClient
import redis
import os
import json
from confluent_kafka import Producer, Consumer, KafkaError

# Настройка базы данных PostgreSQL
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:secret@localhost:5432/conference_db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Настройка MongoDB
MONGO_URI = "mongodb://root:pass@localhost:27017/"
mongo_client = MongoClient(MONGO_URI)
mongo_db = mongo_client["conference_db"]
mongo_users_collection = mongo_db["users"]

# Настройка Redis
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

# Настройки Kafka
KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
KAFKA_TOPIC = "conference-events"

# Секретный ключ для подписи JWT
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

app = FastAPI()

# Настройка паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Настройка OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Kafka Producer
producer = Producer({"bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS})

# Модели данных PostgreSQL
class ReportDB(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    content = Column(String)
    author_id = Column(Integer)

class ConferenceDB(Base):
    __tablename__ = "conferences"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)

class ConferenceReportDB(Base):
    __tablename__ = "conference_reports"

    id = Column(Integer, primary_key=True, index=True)
    conference_id = Column(Integer, ForeignKey("conferences.id"))
    report_id = Column(Integer, ForeignKey("reports.id"))

Base.metadata.create_all(bind=engine)

# Pydantic схемы
class User(BaseModel):
    id: Optional[str]
    username: str
    email: str
    hashed_password: Optional[str]

class Report(BaseModel):
    id: int
    title: str
    content: str
    author_id: int

    class Config:
        orm_mode = True

class Conference(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True

# Утилиты для работы с токенами
async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Получает текущего пользователя из токена."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        return username
    except JWTError:
        raise credentials_exception

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Создает JWT токен с указанным сроком действия."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# Маршруты для MongoDB
@app.post("/users", response_model=User)
def create_user(user: User):
    """Создает нового пользователя в MongoDB."""
    user_dict = user.dict()
    user_dict["hashed_password"] = pwd_context.hash(user_dict["hashed_password"])
    user_id = mongo_users_collection.insert_one(user_dict).inserted_id
    user_dict["id"] = str(user_id)
    return user_dict

@app.get("/users/{username}", response_model=User)
def get_user_by_username(username: str):
    """Возвращает информацию о пользователе по логину из MongoDB."""
    user = mongo_users_collection.find_one({"username": username})
    if user:
        user["id"] = str(user["_id"])
        return user
    raise HTTPException(status_code=404, detail="User not found")

# Маршруты для PostgreSQL
@app.post("/reports", response_model=Report)
def create_report(report: Report):
    """Создает новый доклад."""
    db = SessionLocal()
    db_report = ReportDB(**report.dict())
    db.add(db_report)
    db.commit()
    db.refresh(db_report)

    # Публикация события в Kafka
    producer.produce(KAFKA_TOPIC, key="report_created", value=json.dumps(report.dict()))
    producer.flush()

    # Обновление кеша
    cache_key = "reports"
    reports = db.query(ReportDB).all()
    redis_client.set(cache_key, json.dumps([report.dict() for report in reports]))

    db.close()
    return db_report

@app.get("/reports", response_model=List[Report])
def get_reports():
    """Возвращает список всех докладов с использованием кеша Redis."""
    cache_key = "reports"
    cached_reports = redis_client.get(cache_key)

    if cached_reports:
        return [Report(**report) for report in json.loads(cached_reports)]

    db = SessionLocal()
    reports = db.query(ReportDB).all()
    redis_client.set(cache_key, json.dumps([report.dict() for report in reports]))
    db.close()

    return reports

@app.post("/conferences", response_model=Conference)
def create_conference(conference: Conference):
    """Создает новую конференцию."""
    db = SessionLocal()
    db_conference = ConferenceDB(**conference.dict())
    db.add(db_conference)
    db.commit()
    db.refresh(db_conference)

    # Публикация события в Kafka
    producer.produce(KAFKA_TOPIC, key="conference_created", value=json.dumps(conference.dict()))
    producer.flush()

    db.close()
    return db_conference

@app.post("/conferences/{conference_id}/reports/{report_id}")
def add_report_to_conference(conference_id: int, report_id: int):
    """Добавляет доклад в указанную конференцию."""
    db = SessionLocal()
    db_entry = ConferenceReportDB(conference_id=conference_id, report_id=report_id)
    db.add(db_entry)
    db.commit()

    # Публикация события в Kafka
    producer.produce(KAFKA_TOPIC, key="report_added_to_conference", value=json.dumps({"conference_id": conference_id, "report_id": report_id}))
    producer.flush()

    db.close()
    return {"message": "Report added to conference"}

@app.get("/conferences/{conference_id}/reports", response_model=List[Report])
def get_reports_in_conference(conference_id: int):
    """Возвращает список всех докладов в указанной конференции."""
    db = SessionLocal()
    report_ids = db.query(ConferenceReportDB.report_id).filter(ConferenceReportDB.conference_id == conference_id).all()
    reports = db.query(ReportDB).filter(ReportDB.id.in_([r[0] for r in report_ids])).all()
    db.close()
    return reports
