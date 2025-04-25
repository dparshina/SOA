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
    
@api.get("/posts/{post_id}/view")
def viewPost(request: Request, post_id: int, user_id: int):
    connection = get_grpc()
    try:
        response = connection.viewPost(post_service_pb2.viewPostRequest(post_id=post_id, user_id = user_id))
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
    
@api.post("/posts/{post_id}/liked")
def likePost(request: Request, post_id: int, user_id: int):
    connection = get_grpc()
    try:
        response = connection.likePost(post_service_pb2.likePostRequest(post_id=post_id, user_id = user_id))
        return {
            "like_id": response.like_id,
            "post_id": response.post_id,
            "user_id": response.user_id,
            "created_at": response.created_at
        }
    except grpc.RpcError as e:
        status = GRPC_TO_HTTP.get(e.code(), 500)
        raise HTTPException(status_code=status, detail=e.details())
    
@api.post("/posts/{post_id}/comment")
def commentPost(request: Request, post_id: int, user_id: int, text: str):
    connection = get_grpc()
    try:
        response = connection.commentPost(post_service_pb2.commentPostRequest(post_id=post_id, user_id = user_id, text = text))
        return {
            "comment_id": response.comment_id,
            "post_id": response.post_id,
            "user_id": response.user_id,
            "text": response.text,
            "created_at": response.created_at
        }
    except grpc.RpcError as e:
        status = GRPC_TO_HTTP.get(e.code(), 500)
        raise HTTPException(status_code=status, detail=e.details())
    
@api.get("/posts/{post_id}/comment")
def commentsListing(request: Request, offset: int, limit: int, user_id: int, post_id: int):
    connection = get_grpc()
    try:
        response = connection.commentsListing(post_service_pb2.commentsListingRequest(offset=offset, limit=limit, user_id = user_id, post_id = post_id))
        return {"comments": [
            {
                "comment_id": comment.comment_id,
                "post_id": comment.post_id,
                "user_id": comment.user_id,
                "text": comment.text,
                "createt_at": comment.created_at
            } for comment in response.comments
        ]}
    except grpc.RpcError as e:
        status = GRPC_TO_HTTP.get(e.code(), 500)
        raise HTTPException(status_code=status, detail=e.details())
    

@api.post("/register/")
def userRegister(request: Request, user_data: dict):
    connection = get_grpc()
    try:
        response = connection.userRegister(post_service_pb2.userRegisterRequest("user_id": response.user_id, "created_at": response.created_at))
        return {"user_id": response.user_id, "created_at": response.created_at}
    except grpc.RpcError as e:
        status = GRPC_TO_HTTP.get(e.code(), 500)
        raise HTTPException(status_code=status, detail=e.details())
