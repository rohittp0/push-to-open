from datetime import timedelta, datetime
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, responses
from jwt import PyJWTError
from sqlalchemy.orm import Session

from fastapi.security.oauth2 import OAuthFlowsModel
from fastapi.security import OAuth2
from fastapi.security.utils import get_authorization_scheme_param
from starlette import status
from starlette.requests import Request
from starlette.status import HTTP_403_FORBIDDEN

from google_auth.db import get_db
from google_auth.models import TokenData, User
from google_auth.utils import set_up

config = set_up()


class OAuth2PasswordBearerCookie(OAuth2):
    def __init__(
            self,
            token_url: str,
            scheme_name: str = None,
            scopes: dict = None,
            auto_error: bool = True,
    ):
        if not scopes:
            scopes = {}
        flows = OAuthFlowsModel(password={"tokenUrl": token_url, "scopes": scopes})
        super().__init__(flows=flows, scheme_name=scheme_name, auto_error=auto_error)

    async def __call__(self, request: Request) -> Optional[str]:
        header_authorization: str = request.headers.get("Authorization")
        cookie_authorization: str = request.cookies.get("Authorization")

        header_scheme, header_param = get_authorization_scheme_param(
            header_authorization
        )
        cookie_scheme, cookie_param = get_authorization_scheme_param(
            cookie_authorization
        )

        if header_scheme.lower() == "bearer":
            authorization = True
            scheme = header_scheme
            param = header_param

        elif cookie_scheme.lower() == "bearer":
            authorization = True
            scheme = cookie_scheme
            param = cookie_param

        else:
            authorization = False
            scheme = ""
            param = None

        if not authorization or scheme.lower() != "bearer":
            if self.auto_error:
                raise HTTPException(
                    status_code=HTTP_403_FORBIDDEN, detail="Not authenticated"
                )
            else:
                return None

        return param


oauth2_scheme = OAuth2PasswordBearerCookie(token_url="/token", auto_error=False)


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


def ensure_user(user: User):
    if not user:
        return responses.RedirectResponse(url="/google_login_client",
                                          status_code=status.HTTP_307_TEMPORARY_REDIRECT)
    return None
