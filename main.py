from fastapi import FastAPI, Depends
from starlette.middleware.cors import CORSMiddleware

from google_auth import auth
from google_auth.dependencies import get_current_user
from google_auth.models import User

app = FastAPI()

origins = [
    "https://ad.cusat.me",
    "http://localhost",
    "http://localhost:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)


@app.get("/")
def home(current_user: User = Depends(get_current_user)):
    return current_user
