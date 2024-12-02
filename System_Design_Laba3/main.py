from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from pydantic import BaseModel
from typing import Optional
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import List, Optional

app = FastAPI()

# Настройка PostgreSQL
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:secret@db/postgres"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Секретный ключ для подписи JWT
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


# Настройка паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Настройка OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# Модели данных
class User(BaseModel):
    id: int
    f_name: str
    l_name: str
    login: str
    hashed_password: str
    
class Report(BaseModel):
    id: int
    title: str
    description: str
    author_id: int
    
class Conference(BaseModel):
    id: int
    name: str
    reports: List[int] = []


# SQLAlchemy models
class UserDB(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    login = Column(String, unique=True, index=True)
    first_name = Column(String)
    last_name = Column(String)
    hashed_password = Column(String)


class ReportDB(Base):
    __tablename__ = "reports"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    author_id = Column(Integer, ForeignKey("users.id"))
    description = Column(String, index=True)


class ConferenceDB(Base):
    __tablename__ = "conferences"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String, index=True)
    reports_list = Column(String)


# Зависимости для получения текущего пользователя
async def get_current_user(token: str = Depends(oauth2_scheme)):
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


# Создание и проверка JWT токенов
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# Маршрут для получения токена
@app.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    db = SessionLocal()
    user = db.query(UserDB).filter(UserDB.login == form_data.username).first()
    db.close()

    if user and pwd_context.verify(form_data.password, user.hashed_password):
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.login}, expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )


# Создание нового пользователя
@app.post("/users", response_model=User)
def create_user(user: User, current_user: str = Depends(get_current_user)):
    db = SessionLocal()
    db_user = UserDB(**user.dict())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    db.close()
    return user


# Поиск пользователя по логину
@app.get("/users/{login}", response_model=User)
def get_user_by_login(login: str, current_user: str = Depends(get_current_user)):
    db = SessionLocal()
    user = db.query(UserDB).filter(UserDB.login == login).first()
    db.close()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# Создание доклада
@app.post("/products/", response_model=Report)
def create_report(report: Report, current_user: str = Depends(get_current_user)):
    db = SessionLocal()
    db_report = ReportDB(**report.dict())
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    db.close()
    return report


# Получение списка докладов
@app.get("/reports/", response_model=List[Report])
def get_reports(current_user: str = Depends(get_current_user)):
    db = SessionLocal()
    reports = db.query(ReportDB).all()
    db.close()
    return reports


# Создание конференции
@app.post("/conferences/", response_model=Conference)
def create_conference(user_id: int, report_id: int, current_user: str = Depends(get_current_user)):
    db = SessionLocal()
    conference = db.query(ConferenceDB).filter(ConferenceDB.user_id == user_id).first()

    if not conference:
        conference = ConferenceDB(user_id=user_id, reports_list=str([report_id]))
        db.add(conference)
    else:
        current_report_ids = conference.reports_list.split(",")
        if str(report_id) not in current_report_ids:
            current_report_ids.append(str(report_id))
            conference.reports_list = ",".join(current_report_ids)


    db.commit()
    db.refresh(conference)
    db.close()
    return conference


# Получение конференции пользователя
@app.get("/conferences/{user_id}", response_model=Conference)
def get_conference(user_id: int, current_user: str = Depends(get_current_user)):
    db = SessionLocal()
    conference = db.query(ConferenceDB).filter(ConferenceDB.user_id == user_id).first()
    db.close()

    if conference is None:
        raise HTTPException(status_code=404, detail="Cart not found")

    return conference


