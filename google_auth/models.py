from datetime import datetime

from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from google_auth.db import Base, engine


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    id: int = None
    email: str = None


class User(Base):
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(20), index=True, nullable=False)
    max_unlock = Column(Integer, nullable=False, default=0)
    is_admin = Column(Integer, nullable=False, default=False)


class Unlocks(Base):
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey(User.id))
    user = relationship("User", backref="Unlocks", foreign_keys="Unlocks.user_id")
    date = Column(DateTime, default=datetime.now)


Base.metadata.create_all(bind=engine)
