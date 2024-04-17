import pytest
import shutil
import json
from pytest import FixtureRequest
from pathlib import Path
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import WSGITransport
from server import *


@pytest.fixture
def client():
    client = TestClient(app)
    test_db = Database(
            lambda x: x,
            lambda x, y: x == y,
            {55:["alice"]},
            {55: "password55"}
            )
    app.dependency_overrides[get_db] = lambda: test_db
    yield client

def test_getID():
    id = getID()
    assert 0 <= id and id <= 65535
    
def test_unsigned_short_pos():
    val = unsigned_short(32344)
    assert val == 32344
    
def test_unsigned_short_neg():
    val = unsigned_short(-13434)
    assert val == 52102
    
class GroupIDs:
    def __contains__(self, key: int):
        return 0 <= key <= 35000
             
def test_generate_id():
    id = generate_group_id(GroupIDs())
    assert 35000 < id
    
def test_join_group_ok(client: TestClient):
    res = client.post("/join", json={"username": "john", "password": "password", "groupID": 55})
    assert res.status_code == 200
    assert res.json() == {"message": "OK"}
    
def test_join_group_not_found(client: TestClient):
    res = client.post("/join", json={"username": "john", "password": "password", "groupID": 65})
    assert res.status_code == 404
    assert res.json() == {"detail": "Group 65 not found!"}
    
def test_join_group_unauthorized(client: TestClient):
    res = client.post("/join", json={"username": "john", "password": "pswd", "groupID": 55})
    assert res.status_code == 401
    assert res.json() == {"detail": "Wrong groupID or password!"}
    
def test_join_group_conflict(client: TestClient):
    res = client.post("/join", json={"username": "alice", "password": "password", "groupID": 55})
    assert res.status_code == 409
    assert res.json() == {"detail": "alice already exists!"}
    
def test_create_group(client: TestClient):
    res = client.post("/group/create", json={"password":"mypass"})
    data = res.json()
    assert res.status_code == 200
    assert "groupID" in data
    assert 0 <= data["groupID"] <= 65535
    
def test_get_members(client: TestClient):
    res = client.post("/group/members", json={"password": "password", "groupID": 55})
    assert res.status_code == 200
    assert res.json() == {"members": ["alice"]}
    
def test_get_members_not_found(client: TestClient):
    res = client.post("/group/members", json={"password": "password", "groupID": 56})
    assert res.status_code == 404
    assert res.json() == {"detail": "Group 56 not found!"}
    
def test_get_members_unauthorized(client: TestClient):
    res = client.post("/group/members", json={"password": "pswd", "groupID": 55})
    assert res.status_code == 401
    assert res.json() == {"detail": "Wrong groupID or password!"}
    
def test_get_members_new_members(client: TestClient):
    client.post("/join", json={"username": "john", "password": "password", "groupID": 55})
    res = client.post("/group/members", json={"password": "password", "groupID": 55})
    assert res.status_code == 200
    assert res.json() == {"members": ["alice", "john"]}