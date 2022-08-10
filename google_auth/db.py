import typing

import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, as_declarative, declared_attr

from google_auth.utils import set_up

metadata = sqlalchemy.MetaData()

class_registry = {}


@as_declarative(class_registry=class_registry)
class Base:
    id: typing.Any
    __name__: str

    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()


def get_db():
    db = None
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


engine = create_engine(set_up()["db"], connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
