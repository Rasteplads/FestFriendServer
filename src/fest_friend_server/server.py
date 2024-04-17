from fastapi import FastAPI, HTTPException, status, Request, Depends
from typing import Annotated, Callable, Iterable
import bcrypt
import random
from pydantic import BaseModel


class Database:
    def __init__(
        self,
        hash_func: Callable[[str], bytes],
        check_func: Callable[[str, bytes], bool],
        groups: dict = None,
        groups_login: dict = None,
    ) -> None:
        self.hash_pass = hash_func
        self.check_pass = check_func
        self.groups: dict[int, list[str]] = groups
        self.group_login: dict[int, str] = groups_login

        if self.groups is None:
            self.groups = dict()
        if self.group_login is None:
            self.group_login = dict()


class CreateGroup(BaseModel):
    password: str


class GetMembers(CreateGroup):
    groupID: int


class JoinGroup(GetMembers):
    username: str


def get_id():
    return random.randint(0, 65535)


def unsigned_short(val: int):
    if val < 0:
        return val + (1 << 16)
    return val


def generate_group_id(group_ids: Iterable[str]):
    group_id = get_id()
    while group_id in group_ids:
        group_id = get_id()
    return group_id


def hash_password(password: str):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12))


def check_password(password: str, group_hash: bytes):
    return bcrypt.checkpw(password.encode(), group_hash)


def is_duplicate_user(username: str, usernames: list[str]):
    return username in usernames


app = FastAPI()
database = Database(hash_password, check_password)


async def get_db():
    return database


@app.middleware("http")
async def log_requests(request: Request, call_next):
    body = await request.body()
    print(f"Request: {request.method} {request.url.path} - Body: {body}")
    response = await call_next(request)
    return response


@app.post("/join")
async def join_group(body: JoinGroup, db: Annotated[Database, Depends(get_db)]):
    group_id = unsigned_short(body.groupID)
    username = body.username
    password = body.password
    if group_id not in db.group_login:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Group {group_id} not found!"
        )

    if not db.check_pass(password + str(group_id), db.group_login[group_id]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Wrong groupID or password!",
        )

    if is_duplicate_user(username, db.groups[group_id]):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=f"{username} already exists!"
        )

    db.groups[group_id].append(username)

    return {"message": "OK"}


@app.post("/group/create")
async def create_group(body: CreateGroup, db: Annotated[Database, Depends(get_db)]):
    password = body.password
    group_id = generate_group_id(db.group_login.values())
    hashed = db.hash_pass(password + str(group_id))
    db.group_login[group_id] = hashed
    db.groups[group_id] = []
    return {"groupID": group_id}


@app.post("/group/members")
async def get_members(body: GetMembers, db: Annotated[Database, Depends(get_db)]):
    group_id = unsigned_short(body.groupID)
    password = body.password
    if group_id not in db.group_login:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Group {group_id} not found!"
        )

    if not db.check_pass(password + str(group_id), db.group_login[group_id]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Wrong groupID or password!",
        )

    return {"members": db.groups[group_id]}
