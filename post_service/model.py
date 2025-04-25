from sqlalchemy import Column, Integer, String, Boolean, DateTime, ARRAY, ForeignKey, Date
from sqlalchemy.orm import declarative_base
from sqlalchemy import UniqueConstraint
from datetime import datetime

Base = declarative_base()

class Post(Base):
    __tablename__ = "posts"

    post_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    user_id = Column(Integer, nullable=False)
    create_time = Column(DateTime, default=datetime.utcnow)
    last_update = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, default=None)
    is_private = Column(Boolean, default=False)
    tags = Column(ARRAY(String), default=[])

class Like(Base):
    __tablename__ = "likes"

    like_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    post_id = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    deleted_at = Column(DateTime, default=None)

    __table_args__ = (
        UniqueConstraint('user_id', 'post_id', name='unique_user_post_like'),
    )

class Comment(Base):
    __tablename__ = "comments"

    comment_id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(Integer, nullable=False)
    user_id = Column(Integer, nullable=False)
    text = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    deleted_at = Column(DateTime, default=None)

class User(Base):
    __tablename__ = 'users'

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    lastname = Column(String, nullable=False)
    firstname = Column(String, nullable=False)
    username = Column(String, unique=True, nullable=False)
    age = Column(Integer, nullable=True) 
    email = Column(String, unique=True, nullable=False)
    phone = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    lastLogin = Column(DateTime, default=datetime.utcnow)
    birthDay = Column(Date, nullable=True)

    def __repr__(self):
        return f"<User(username={self.username}, email={self.email})>"