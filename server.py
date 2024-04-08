from fastapi import FastAPI, HTTPException, status
import bcrypt
import random
import string
from pydantic import BaseModel

app = FastAPI()

groups: dict[str, list[str]] = dict()
groupLogin: dict[str, str] = dict()

class CreateGroup(BaseModel):
    password: str

class GetMembers(CreateGroup):
    groupID: str

class JoinGroup(GetMembers):
    username: str


def getID():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

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
    
@app.post("/join")
async def join_group(body: JoinGroup):
    groupID = body.groupID
    username = body.username
    password = body.password
    if groupID not in groupLogin:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Group {groupID} not found!")
    
    if not check_password(password + groupID, groupLogin[groupID]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Wrong groupID or password!")
    
    if is_duplicate_user(username, groups[groupID]):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"{username} already exists!")
    
    groups[groupID].append(username)
    
    return {"message": "OK"}
    
@app.post("/group/create")
async def create_group(body: CreateGroup):
    password = body.password
    groupID = generate_group_id(groupLogin.values())
    hashed = hash_password(password + groupID)
    groupLogin[groupID] = hashed
    groups[groupID] = []
    return {"groupID": groupID}

@app.post("/group/members")
async def get_members(body: GetMembers):
    groupID = body.groupID
    password = body.password
    if groupID not in groupLogin:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Group {groupID} not found!")
    
    if not check_password(password + groupID, groupLogin[groupID]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Wrong groupID or password!")
    
    return {"members": groups[groupID]}