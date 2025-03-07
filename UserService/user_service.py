from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import uvicorn
from pydantic import BaseModel
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from config import settings
from sqlalchemy.orm import Session
from db import SessionLocal, engine, Base
from model import User as UserModel
from sqlalchemy.future import select
from contextlib import asynccontextmanager

pass_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oath = OAuth2PasswordBearer(tokenUrl="token")


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(lifespan=lifespan)

app.title = "User Service"


@app.get("/")
async def root():
    return {"message": "Hello, I am user service!"}


class User(BaseModel):
    id: int
    lastName: str
    firstName: str
    username: str
    age: int or None = None
    email: str
    phone: str
    lastLogin: datetime
    birthDay: datetime or None = None


class UserInDB(User):
    hashed_password: str


class UserRegister(BaseModel):
    username: str
    password: str
    email: str
    firstName: str = None
    lastName: str = None
    birthDay: datetime = None
    phone: str = None


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str


async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()  


def get_hash(password):
    return pass_context.hash(password)


def get_from_db(db, username):
    return db.query(UserModel).filter(UserModel.username == username).first()


def authenticate(db, username, password):
    user = get_from_db(db, username)
    if not user:
        return False
    if not pass_context.verify(password, user.hashed_password):
        return False
    return user


def create_acc_token(data: dict, expires: timedelta or None = None):
    data_change = data.copy()
    if expires:
        exp = datetime.utcnow() + expires
    else:
        exp = datetime.utcnow() + timedelta(minutes=5)
    data_change.update({"exp": exp})
    enc_jwt = jwt.encode(data_change, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return enc_jwt


@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Incorrect username or password")
    access_token = create_acc_token(
        data={"sub": user.username}, expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE))
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/register", response_model=User)
async def register_user(user: UserRegister, db: Session = Depends(get_db)):
    stmt = select(UserModel).where(UserModel.username == user.username)
    result = await db.execute(stmt)
    db_user = result.scalar_one_or_none()

    if db_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already registered")

    new_user = UserModel(
        username=user.username,
        email=user.email,
        hashed_password=get_hash(user.password),
        firstName=user.firstName,
        lastName=user.lastName,
        birthDay=user.birthDay,
        phone=user.phone,
        lastLogin=datetime.utcnow()
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@app.put("/profile", response_model=User)
async def update_user_profile(user: UserRegister, db: Session = Depends(get_db), token: str = Depends(oath)):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        user_data = get_from_db(db, username)
        if not user_data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user_data.firstName = user.firstName
    user_data.lastName = user.lastName
    user_data.birthDay = user.birthDay
    user_data.email = user.email
    user_data.phone = user.phone
    user_data.lastLogin = datetime.utcnow()

    db.commit()
    db.refresh(user_data)

    return user_data


@app.get("/profile", response_model=User)
async def get_user_profile(token: str = Depends(oath), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        user_data = get_from_db(db, username)
        if not user_data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    return user_data


if __name__ == "__main__":
    uvicorn.run(app, port=8001)
