from fastapi import FastAPI, HTTPException, status, Request
import bcrypt
import random
import string
from pydantic import BaseModel

app = FastAPI()

groups: dict[str, list[str]] = dict()
groupLogin: dict[str, int] = dict()

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
    print(groupID)
    return groupID
    
def hash_password(password: str):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12))
    
def check_password(password: str, grouphash: str):
    return bcrypt.checkpw(password.encode(), grouphash)

def is_duplicate_user(username: str, usernames: list[str]):
    return username in usernames
    
@app.middleware("http")
async def log_requests(request: Request, call_next):
    body = await request.body()
    print(f"Request: {request.method} {request.url.path} - Body: {body}")
    response = await call_next(request)
    return response
    
@app.post("/join")
async def join_group(body: JoinGroup):
    groupID = unsigned_short(body.groupID)
    username = body.username
    password = body.password
    if groupID not in groupLogin:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Group {groupID} not found!")
    
    if not check_password(password + str(groupID), groupLogin[groupID]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Wrong groupID or password!")
    
    if is_duplicate_user(username, groups[groupID]):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"{username} already exists!")
    
    groups[groupID].append(username)
    
    return {"message": "OK"}
    
@app.post("/group/create")
async def create_group(body: CreateGroup):
    password = body.password
    groupID = generate_group_id(groupLogin.values())
    hashed = hash_password(password + str(groupID))
    groupLogin[groupID] = hashed
    groups[groupID] = []
    return {"groupID": groupID}

@app.post("/group/members")
async def get_members(body: GetMembers):
    groupID = unsigned_short(body.groupID)
    password = body.password
    if groupID not in groupLogin:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Group {groupID} not found!")
    
    if not check_password(password + str(groupID), groupLogin[groupID]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Wrong groupID or password!")
    
    return {"members": groups[groupID]}