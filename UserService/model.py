from sqlalchemy import Column, Integer, String, Date, DateTime
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    lastname = Column(String, nullable=False)
    firstname = Column(String, nullable=False)
    username = Column(String, unique=True, nullable=False)
    age = Column(Integer, nullable=True) 
    email = Column(String, unique=True, nullable=False)
    phone = Column(String, nullable=False)
    lastLogin = Column(DateTime, default=datetime.utcnow)
    birthDay = Column(Date, nullable=True)

    def __repr__(self):
        return f"<User(username={self.username}, email={self.email})>"
