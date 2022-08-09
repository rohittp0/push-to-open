from datetime import timedelta, datetime

import jwt
from fastapi import Depends, HTTPException
from jwt import PyJWTError
from sqlalchemy.orm import Session
from starlette.status import HTTP_403_FORBIDDEN

from google_auth.db import get_db, User
from google_auth.models import OAuth2PasswordBearerCookie, TokenData
from google_auth.utils import set_up

oauth2_scheme = OAuth2PasswordBearerCookie(token_url="/token")
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
    credentials_exception = HTTPException(
        status_code=HTTP_403_FORBIDDEN, detail="Could not validate credentials"
    )
    try:
        payload = jwt.decode(token, config["secret"], algorithms=["HS256"])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except PyJWTError:
        raise credentials_exception
    user = get_user_by_email(email=token_data.email)
    if user is None:
        raise credentials_exception
    return user


# class BasicAuth(SecurityBase):
#     def __init__(self, scheme_name: str = None, auto_error: bool = True):
#         self.scheme_name = scheme_name or self.__class__.__name__
#         self.auto_error = auto_error
#
#     async def __call__(self, request: Request) -> Optional[str]:
#         authorization: str = request.headers.get("Authorization")
#         scheme, param = get_authorization_scheme_param(authorization)
#         if not authorization or scheme.lower() != "basic":
#             if self.auto_error:
#                 raise HTTPException(
#                     status_code=HTTP_403_FORBIDDEN, detail="Not authenticated"
#                 )
#             else:
#                 return None
#         return param
#
#
# basic_auth = BasicAuth(auto_error=False)
