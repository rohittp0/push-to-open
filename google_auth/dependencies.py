from datetime import timedelta, datetime

import jwt
from fastapi import Depends
from jwt import PyJWTError
from sqlalchemy.orm import Session

from google_auth.db import get_db, User
from google_auth.models import OAuth2PasswordBearerCookie, TokenData
from google_auth.utils import set_up

oauth2_scheme = OAuth2PasswordBearerCookie(token_url="/token", auto_error=False)
config = set_up()


def get_user_by_email(email: str, db: Session = None):
    if not db:
        db = next(get_db())
    return db.query(User).filter(User.email == email).first()


def authenticate_user_email(email: str):
    db = next(get_db())
    user = get_user_by_email(email, db)
    if not user:
        user = User(email=email)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def create_access_token(*, data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, config["secret"], algorithm="HS256")
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, config["secret"], algorithms=["HS256"])
        email: str = payload.get("sub")
        if email is None:
            return None
        token_data = TokenData(email=email)
    except PyJWTError:
        return None
    user = get_user_by_email(email=token_data.email)

    return user

