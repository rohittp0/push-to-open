from datetime import timedelta, datetime

from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from starlette import status
from starlette.middleware.cors import CORSMiddleware
from starlette import responses
from starlette.websockets import WebSocket, WebSocketDisconnect

from google_auth import auth
from google_auth.db import get_db
from google_auth.models import User, Unlocks
from google_auth.dependencies import get_current_user, ensure_user

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

lock_socket: WebSocket | None = None


async def unlock_door():
    if not lock_socket:
        return False

    await lock_socket.send_text("OPEN")
    return True


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    global lock_socket
    lock_socket = websocket
    try:
        while True:
            print(await websocket.receive_text())
    except WebSocketDisconnect:
        lock_socket = None


@app.get("/make_admin")
def make_admin(email: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if ensure_user(user):
        return ensure_user(user)

    is_admin = user.is_admin or user.email == "tprohit9@gmail.com"

    if not is_admin:
        return responses.PlainTextResponse(content="You are not allowed to do that",
                                           status_code=status.HTTP_400_BAD_REQUEST)

    client: User = db.query(User).filter(User.email == email).first()

    client.is_admin = True
    db.commit()

    return responses.PlainTextResponse(content="Done 👍")


@app.get("/award")
def add_unlocks(email: str, unlocks: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if ensure_user(user):
        return ensure_user(user)

    if not user or not user.is_admin:
        return responses.PlainTextResponse(content="You are not allowed to do that",
                                           status_code=status.HTTP_400_BAD_REQUEST)

    client: User = db.query(User).filter(User.email == email).first()

    if not client:
        responses.PlainTextResponse(content="User not found",
                                    status_code=status.HTTP_400_BAD_REQUEST)

    client.max_unlock = unlocks
    db.commit()

    return responses.PlainTextResponse(content="Done 👍")


@app.get("/")
async def home(user: User | None = Depends(get_current_user), db: Session = Depends(get_db)):
    if ensure_user(user):
        return ensure_user(user)

    if user.max_unlock <= 0 and not user.is_admin:
        return responses.PlainTextResponse(content="Maximum unlock limit reached",
                                           status_code=status.HTTP_400_BAD_REQUEST)

    num_unlocks = db.query(Unlocks).filter(Unlocks.user == user,
                                           (Unlocks.date + timedelta(days=1)) > datetime.now()).count()

    if not user.is_admin and num_unlocks >= user.max_unlock:
        return responses.PlainTextResponse(content=f"Maximum unlock limit reached, limit: {user.max_unlock}",
                                           status_code=status.HTTP_400_BAD_REQUEST)

    if not await unlock_door():
        return responses.PlainTextResponse(content=f"Device offline please try again later",
                                           status_code=status.HTTP_404_NOT_FOUND)

    unlock = Unlocks(user_id=user.id)
    db.add(unlock)
    db.commit()

    return responses.PlainTextResponse(content=f"Door unlocked, {user.max_unlock - num_unlocks} unlocks remaining")
