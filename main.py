from asyncio import sleep
from typing import List

from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from starlette import status
from starlette.middleware.cors import CORSMiddleware
from starlette import responses
from starlette.websockets import WebSocket, WebSocketDisconnect

from google_auth import auth
from google_auth.db import get_db, User
from google_auth.dependencies import get_current_user

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


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


manager = ConnectionManager()


async def unlock_door():
    await manager.broadcast("OPEN")
    await sleep(3)
    await manager.broadcast("CLOSE")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            print(await websocket.receive_text())
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.get("/award")
def add_unlocks(email: str, unlocks: int,user: User = Depends(get_current_user)):
    if not user or not user.is_admin:
        return responses.PlainTextResponse(content="You are not allowed to do that",
                                           status_code=status.HTTP_400_BAD_REQUEST)

    db: Session = next(get_db())

    client: User = db.query(User).filter(User.email == email).first()

    if not client:
        responses.PlainTextResponse(content="User not found",
                                    status_code=status.HTTP_400_BAD_REQUEST)

    client.max_unlock = unlocks
    db.commit()

    return responses.PlainTextResponse(content="Done 👍")


@app.get("/")
async def home(user: User | None = Depends(get_current_user)):
    if not user:
        return responses.RedirectResponse(url="/google_login_client",
                                          status_code=status.HTTP_307_TEMPORARY_REDIRECT)

    # if user.max_unlock <= 0 and not user.is_admin:
    #     return responses.PlainTextResponse(content="Maximum unlock limit reached",
    #                                        status_code=status.HTTP_400_BAD_REQUEST)

    if not user.is_admin:
        db: Session = next(get_db())

        user = db.query(User).filter(User.id == user.id).first()
        user.max_unlock -= 1

        db.commit()
        db.refresh(user)

    await unlock_door()

    return responses.PlainTextResponse(content=f"Door unlocked, {user.max_unlock} unlocks remaining")
