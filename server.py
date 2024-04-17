from fastapi import FastAPI, HTTPException, status, Request, Depends
from typing import Annotated, Callable
import bcrypt
import random
from pydantic import BaseModel

class Database:
    def __init__(self, hash_func: Callable[[str], str], check_func: Callable[[str, str], bool], groups: dict = None, groupsLogin: dict = None) -> None:
        self.hash_pass = hash_func
        self.check_pass = check_func
        self.groups: dict[int, list[str]] = groups
        self.groupLogin: dict[int, str] = groupsLogin
        
        if self.groups is None:
            self.groups = dict()
        if self.groupLogin is None:
            self.groupLogin = dict()
            

class CreateGroup(BaseModel):
    password: str

class GetMembers(CreateGroup):
    groupID: int

class JoinGroup(GetMembers):
    username: str

def getID():
    return random.randint(0, 65535)

def unsigned_short(val: int):
    if val < 0:
        return val + (1 << 16)
    return val

def generate_group_id(groupIDs: list[str]):
    groupID = getID()
    while groupID in groupIDs:
        groupID = getID()
    return groupID
    
def hash_password(password: str):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12))
    
def check_password(password: str, grouphash: str):
    return bcrypt.checkpw(password.encode(), grouphash)

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
    groupID = unsigned_short(body.groupID)
    username = body.username
    password = body.password
    if groupID not in db.groupLogin:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Group {groupID} not found!")
    
    if not db.check_pass(password + str(groupID), db.groupLogin[groupID]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Wrong groupID or password!")
    
    if is_duplicate_user(username, db.groups[groupID]):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"{username} already exists!")
    
    db.groups[groupID].append(username)
    
    return {"message": "OK"}
    
@app.post("/group/create")
async def create_group(body: CreateGroup, db: Annotated[Database, Depends(get_db)]):
    password = body.password
    groupID = generate_group_id(db.groupLogin.values())
    hashed = db.hash_pass(password + str(groupID))
    db.groupLogin[groupID] = hashed
    db.groups[groupID] = []
    return {"groupID": groupID}

@app.post("/group/members")
async def get_members(body: GetMembers, db: Annotated[Database, Depends(get_db)]):
    groupID = unsigned_short(body.groupID)
    password = body.password
    if groupID not in db.groupLogin:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Group {groupID} not found!")
    
    if not db.check_pass(password + str(groupID), db.groupLogin[groupID]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Wrong groupID or password!")
    
    return {"members": db.groups[groupID]}