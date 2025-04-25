import pytest
from fastapi.testclient import TestClient
from API_gateway.proxy_service import api
from API_gateway.model import PostCreate
import json

client = TestClient(api)

post_data = PostCreate(
    title="fghfgjfjgf", 
    description="lkjfgdlkfgj",
    user_id = 1,
    is_private=True,
    tags=["ljfgdk", "jkdfgdk"]
)

post_update = PostCreate(
    title="utyeutyrutyiu", 
    description="iruteroitu",
    user_id = 1,
    is_private=True,
    tags=["kjhfksj", "ituerotiu"]
)

def testPostCreate():
    global post_id 
    response = client.post("/posts", json=post_data.model_dump())
    assert response.status_code == 200
    json_response = response.json()
    post_id = int(json_response["post_id"])
    assert "post_id" in json_response
    assert json_response["post_id"] > 0

def testPostGet():
    response = client.get(f"/posts/{post_id}?user_id=1")
    assert response.status_code == 200
    json_response = response.json()
    assert json_response["title"] == 'fghfgjfjgf'
    assert json_response["description"] == "lkjfgdlkfgj"

def testpostsListing():
    response = client.post("/posts", json=post_data.model_dump())
    response = client.get("/posts?limit=2&offset=0&user_id=1")
    assert response.status_code == 200
    json_response = response.json()
    assert "posts" in json_response
    assert len(json_response["posts"]) == 2

def testUnauthorizedViewing():
    response = client.get(f"/posts/{post_id}?user_id=2")
    assert response.status_code == 403

def testPostUpdate():
    response = client.put(f"/posts/{post_id}", json=post_update.model_dump())
    assert response.status_code == 200
    json_response = response.json()
    assert "post_id" in json_response
    assert json_response["title"] == "utyeutyrutyiu"

def testPostDelete():
    response1 = client.delete(f"/posts/{post_id}?user_id=1")
    response2 = client.delete(f"/posts/{post_id + 1}?user_id=1")
    assert response1.status_code == 200
    assert response2.status_code == 200
    json_response1 = response1.json()
    json_response2 = response2.json()
    assert "post_id" in json_response1
    assert "post_id" in json_response2
    assert json_response1["post_id"] == post_id
    assert json_response2["post_id"] == post_id + 1

