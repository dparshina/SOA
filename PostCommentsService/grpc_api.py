import grpc
from proto import post_service_pb2
from proto import post_service_pb2_grpc
from datetime import datetime
from config import settings
from model import Post
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import settings

engine = create_engine(settings.DATABASE_URL)
Session = sessionmaker(bind=engine)

class postService(post_service_pb2_grpc.postServiceServicer):
    def postCreate(self, request, context):
        db = Session()
        new_post = Post(
            title=request.title,
            description=request.description,
            user_id=request.user_id,
            create_time=datetime.utcnow(),
            last_update=datetime.utcnow(),
            is_private=request.is_private,
            tags=request.tags
        )
        db.add(new_post)
        db.commit()
        db.refresh(new_post)
        db.close()
        return post_service_pb2.postCreateResponse(post_id=new_post.post_id)

    def postGet(self, request, context):
        db = Session()
        post = db.query(Post).filter(Post.post_id == request.post_id).first()
        if not post:
            context.abort(grpc.StatusCode.NOT_FOUND, "Пост не найден")
        if post.is_private and post.user_id != request.user_id:
            context.abort(grpc.StatusCode.PERMISSION_DENIED, "Нет доступа к посту")
        db.close()
        return post_service_pb2.postGetResponse(
            post_id=post.post_id,
            title=post.title,
            description=post.description,
            user_id=post.user_id,
            create_time=str(post.create_time),
            last_update=str(post.last_update),
            is_private=post.is_private,
            tags=post.tags
        )

    def postUpdate(self, request, context):
        db = Session()
        post = db.query(Post).filter(Post.post_id == request.post_id).first()
        if not post:
            context.abort(grpc.StatusCode.NOT_FOUND, "Пост не найден")
        if post.user_id != request.user_id:
            context.abort(grpc.StatusCode.PERMISSION_DENIED, "Нет доступа к посту")
        
        post.title = request.title
        post.description = request.description
        post.last_update = datetime.utcnow()
        post.is_private = request.is_private
        post.tags = request.tags
        db.commit()
        db.refresh(post)
        db.close()
        return post_service_pb2.postUpdateResponse(
            post_id=post.post_id,
            title=post.title,
            description=post.description,
            user_id=post.user_id,
            create_time=str(post.create_time),
            last_update=str(post.last_update),
            is_private=post.is_private,
            tags=post.tags
        )

    def postDelete(self, request, context):
        db = Session()
        post = db.query(Post).filter(Post.post_id == request.post_id).first()
        if not post:
            context.abort(grpc.StatusCode.NOT_FOUND, "Пост не найден")
        if post.user_id != request.user_id:
            context.abort(grpc.StatusCode.PERMISSION_DENIED, "Нет доступа к посту")
        db.delete(post)
        db.commit()
        db.close()
        return post_service_pb2.postDeleteResponse(success=True, post_id=request.post_id)

    def postsListing(self, request, context):
        db = Session()
        posts = db.query(Post).filter(
            (Post.is_private == False) | (Post.user_id == request.user_id)
        ).limit(request.limit).offset(request.offset).all()
        db.close()
        return post_service_pb2.postsListingResponse(
            posts=[
                post_service_pb2.postGetResponse(
                    post_id=post.post_id,
                    title=post.title,
                    description=post.description,
                    user_id=post.user_id,
                    create_time=str(post.create_time),
                    last_update=str(post.last_update),
                    is_private=post.is_private,
                    tags=post.tags
                ) for post in posts
            ]
        )
