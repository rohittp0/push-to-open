from datetime import timedelta

from fastapi import HTTPException, APIRouter
from fastapi.encoders import jsonable_encoder

from google.auth.exceptions import GoogleAuthError

from starlette.responses import JSONResponse, HTMLResponse, RedirectResponse
from starlette.requests import Request

from google.oauth2 import id_token
from google.auth.transport import requests

from google_auth.dependencies import authenticate_user_email, create_access_token
from google_auth.models import Token
from google_auth.utils import set_up, get_login_js

config = set_up()

COOKIE_AUTHORIZATION_NAME = "Authorization"

API_LOCATION = f"{config['protocol']}{config['domain']}:{config['port']}"
SWAP_TOKEN_ENDPOINT = "/swap_token"
SUCCESS_ROUTE = "/"

ACCESS_TOKEN_EXPIRE_MINUTES = 24*60

js_client = get_login_js(
    client_id=config['google']['id'],
    api_location=API_LOCATION,
    swap_token_endpoint=SWAP_TOKEN_ENDPOINT,
    success_route=SUCCESS_ROUTE
)

router = APIRouter()


@router.get("/google_login_client", tags=["security"])
def google_login_client():
    return HTMLResponse(js_client)


@router.post(f"{SWAP_TOKEN_ENDPOINT}", response_model=Token, tags=["security"])
async def swap_token(request: Request = None):
    if not request.headers.get("X-Requested-With"):
        raise HTTPException(status_code=400, detail="Incorrect headers")

    body_bytes = await request.body()
    auth_code = jsonable_encoder(body_bytes)

    try:
        info = id_token.verify_oauth2_token(auth_code, requests.Request(), config["google"]["id"])

        if info['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            raise ValueError('Wrong issuer.')

        if info['email'] and info['email_verified']:
            email = info.get('email')

        else:
            raise HTTPException(status_code=400, detail="Unable to validate social login")

    except GoogleAuthError:
        raise HTTPException(status_code=400, detail="Unable to validate social login")

    authenticated_user = authenticate_user_email(email)

    if not authenticated_user:
        raise HTTPException(status_code=400, detail="Incorrect email address")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": authenticated_user.email}, expires_delta=access_token_expires
    )

    token = jsonable_encoder(access_token)

    response = JSONResponse({"access_token": token, "token_type": "bearer"})

    response.set_cookie(
        COOKIE_AUTHORIZATION_NAME,
        value=f"Bearer {token}",
        domain=config["domain"],
        httponly=True,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES*60,
        expires=ACCESS_TOKEN_EXPIRE_MINUTES*60,
    )
    return response


@router.get("/logout")
async def route_logout_and_remove_cookie():
    response = RedirectResponse(url="/")
    response.delete_cookie("Authorization", domain=config["domain"])
    return response
