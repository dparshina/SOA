from fastapi import FastAPI, HTTPException, Request, Depends, status
import requests
import grpc
import json
from pydantic import BaseModel
from config import settings
import uvicorn
from .model import PostCreate
from proto import post_service_pb2
from proto import post_service_pb2_grpc

GRPC_TO_HTTP = {
    grpc.StatusCode.OK: 200,
    grpc.StatusCode.CANCELLED: 499,
    grpc.StatusCode.UNKNOWN: 500,
    grpc.StatusCode.INVALID_ARGUMENT: 400,
    grpc.StatusCode.DEADLINE_EXCEEDED: 504,
    grpc.StatusCode.NOT_FOUND: 404,
    grpc.StatusCode.ALREADY_EXISTS: 409,
    grpc.StatusCode.PERMISSION_DENIED: 403,
    grpc.StatusCode.UNAUTHENTICATED: 401,
    grpc.StatusCode.RESOURCE_EXHAUSTED: 429,
    grpc.StatusCode.FAILED_PRECONDITION: 400,
    grpc.StatusCode.ABORTED: 409,
    grpc.StatusCode.OUT_OF_RANGE: 400,
    grpc.StatusCode.UNIMPLEMENTED: 501,
    grpc.StatusCode.INTERNAL: 500,
    grpc.StatusCode.UNAVAILABLE: 503,
    grpc.StatusCode.DATA_LOSS: 500,
}

def get_grpc():
    channel = grpc.insecure_channel(settings.POST_SERVICE_URL)
    return post_service_pb2_grpc.postServiceStub(channel)

api = FastAPI()
api.title = "API Gateway"

@api.get("/")
async def root():
    return {"message": "Hello, I am API Gateway!"}

@api.post("/posts/")
def postCreate(request: Request, post: PostCreate):
    connection = get_grpc()
    response = connection.postCreate(post_service_pb2.postCreateRequest(
        title=post.title,
        description=post.description,
        user_id=post.user_id,
        is_private=post.is_private,
        tags=post.tags
    ))

    return {"post_id": response.post_id}

@api.get("/posts/{post_id}")
def postGet(request: Request, post_id: int, user_id: int):
    connection = get_grpc()
    try:
        response = connection.postGet(post_service_pb2.postGetRequest(post_id=post_id, user_id = user_id))
        return {
            "post_id": response.post_id,
            "title": response.title,
            "description": response.description,
            "user_id": response.user_id,
            "create_time": response.create_time,
            "last_update": response.last_update,
            "is_private": response.is_private,
            "tags": list(response.tags)
        }
    except grpc.RpcError as e:
        status = GRPC_TO_HTTP.get(e.code(), 500)
        raise HTTPException(status_code=status, detail=e.details())

@api.delete("/posts/{post_id}")
def postDelete(request: Request, post_id: int, user_id: int):
    connection = get_grpc()
    try:
        response = connection.postDelete(post_service_pb2.postDeleteRequest(post_id=post_id, user_id=user_id))
        return {
            "success": response.success,
            "post_id": response.post_id
        }
    except grpc.RpcError as e:
        status = GRPC_TO_HTTP.get(e.code(), 500)
        raise HTTPException(status_code=status, detail=e.details())

@api.put("/posts/{post_id}")
def postUpdate(request: Request, post_id: int, post: PostCreate):
    connection = get_grpc()
    try:
        response = connection.postUpdate(post_service_pb2.postUpdateRequest(
            post_id=post_id,
            title=post.title,
            description=post.description,
            user_id = post.user_id,
            is_private=post.is_private,
            tags=post.tags
        ))
        return {
            "post_id": response.post_id,
            "title": response.title,
            "description": response.description,
            "user_id": response.user_id,
            "create_time": response.create_time,
            "last_update": response.last_update,
            "is_private": response.is_private,
            "tags": list(response.tags)
        }
    except grpc.RpcError as e:
        status = GRPC_TO_HTTP.get(e.code(), 500)
        raise HTTPException(status_code=status, detail=e.details())

@api.get("/posts/")
def postsListing(request: Request, offset: int, limit: int, user_id: int):
    connection = get_grpc()
    try:
        response = connection.postsListing(post_service_pb2.postsListingRequest(offset=offset, limit=limit, user_id = user_id))
        return {"posts": [
            {
                "post_id": post.post_id,
                "title": post.title,
                "description": post.description,
                "user_id": post.user_id,
                "create_time": post.create_time,
                "last_update": post.last_update,
                "is_private": post.is_private,
                "tags": list(post.tags)
            } for post in response.posts
        ]}
    except grpc.RpcError as e:
        status = GRPC_TO_HTTP.get(e.code(), 500)
        raise HTTPException(status_code=status, detail=e.details())

