from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from datetime import timedelta
from passlib.context import CryptContext
import asyncpg
from typing import List
from app.jwt import create_access_token, get_current_user, ACCESS_TOKEN_EXPIRE_MINUTES
from app.models import User, Report, Conference

app = FastAPI()

DATABASE_URL = "postgresql://myuser:mypassword@localhost/mydatabase"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Подключение к базе данных
async def get_db():
    conn = await asyncpg.connect(DATABASE_URL)
    return conn

# API для авторизации
@app.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: asyncpg.Connection = Depends(get_db)):
    query = "SELECT * FROM users WHERE login = $1"
    user = await db.fetchrow(query, form_data.username)
    if user and pwd_context.verify(form_data.password, user['password']):
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(data={"sub": user['login']}, expires_delta=access_token_expires)
        return {"access_token": access_token, "token_type": "bearer"}
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

# API для управления пользователями
@app.post("/users/", response_model=User)
async def create_user(user: User, db: asyncpg.Connection = Depends(get_db)):
    hashed_password = pwd_context.hash(user.password)
    query = "INSERT INTO users (f_name, l_name, login, password) VALUES ($1, $2, $3, $4) RETURNING id"
    user_id = await db.fetchval(query, user.f_name, user.l_name, user.login, hashed_password)
    user.id = user_id
    return user

@app.get("/users/", response_model=List[User])
async def get_users(db: asyncpg.Connection = Depends(get_db)):
    query = "SELECT * FROM users"
    users = await db.fetch(query)
    return users

@app.get("/users/{login}", response_model=User)
async def get_user_by_login(login: str, db: asyncpg.Connection = Depends(get_db)):
    query = "SELECT * FROM users WHERE login = $1"
    user = await db.fetchrow(query, login)
    if user:
        return user
    else:
        raise HTTPException(status_code=404, detail="User not found")

# API для докладов
@app.post("/reports/", response_model=Report)
async def create_report(report: Report, db: asyncpg.Connection = Depends(get_db)):
    query = "INSERT INTO reports (title, description, author_id) VALUES ($1, $2, $3) RETURNING id"
    report_id = await db.fetchval(query, report.title, report.description, report.author_id)
    report.id = report_id
    return report

@app.get("/reports/", response_model=List[Report])
async def get_reports(db: asyncpg.Connection = Depends(get_db)):
    query = "SELECT * FROM reports"
    reports = await db.fetch(query)
    return reports

# API для конференций
@app.post("/conferences/", response_model=Conference)
async def create_conference(conference: Conference, db: asyncpg.Connection = Depends(get_db)):
    query = "INSERT INTO conferences (name, reports) VALUES ($1, $2) RETURNING id"
    conference_id = await db.fetchval(query, conference.name, conference.reports)
    conference.id = conference_id
    return conference

@app.get("/conferences/", response_model=List[Conference])
async def get_conferences(db: asyncpg.Connection = Depends(get_db)):
    query = "SELECT * FROM conferences"
    conferences = await db.fetch(query)
    return conferences
