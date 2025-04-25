import grpc
from proto import post_service_pb2
from proto import post_service_pb2_grpc
from datetime import datetime
from config import settings
from model import Post, Like, Comment, User
from sqlalchemy import create_engine, exists
from sqlalchemy.orm import sessionmaker
from config import settings
from kafka_producer import KafkaProducer

engine = create_engine(settings.DATABASE_URL)
Session = sessionmaker(bind=engine)
kafka_producer = KafkaProducer()

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
        post = db.query(Post).filter(Post.post_id == request.post_id and Post.deleted_at == None).first()
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
        post = db.query(Post).filter(Post.post_id == request.post_id and Post.deleted_at == None).first()
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
        post = db.query(Post).filter(Post.post_id == request.post_id and Post.deleted_at == None).first()
        if not post:
            context.abort(grpc.StatusCode.NOT_FOUND, "Пост не найден")
        if post.user_id != request.user_id:
            context.abort(grpc.StatusCode.PERMISSION_DENIED, "Нет доступа к посту")
        post.deleted_at = datetime.utcnow()
        db.commit()
        db.refresh(post)

        likes_exist = db.query(exists().where(
        Like.post_id == request.post_id,
            Like.deleted_at.is_(None)
        )).scalar()

        if likes_exist:
            db.query(Like).filter(
                Like.post_id == request.post_id,
                Like.deleted_at.is_(None)
            ).update({"deleted_at": datetime.utcnow()})

        comments_exist = db.query(exists().where(
            Comment.post_id == request.post_id,
            Comment.deleted_at.is_(None)
        )).scalar()

        if comments_exist:
            db.query(Comment).filter(
                Comment.post_id == request.post_id,
                Comment.deleted_at.is_(None)
            ).update({"deleted_at": datetime.utcnow()})

        db.commit()
        db.close()
        return post_service_pb2.postDeleteResponse(success=True, post_id=request.post_id)

    def postsListing(self, request, context):
        db = Session()
        posts = db.query(Post).filter(
            (Post.is_private == False and Post.deleted_at == None) | (Post.user_id == request.user_id and Post.deleted_at == None)
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
    
    def viewPost(self, request, context):
        db = Session()
        post = db.query(Post).filter(Post.post_id == request.post_id and Post.deleted_at == None).first()
        if not post:
            context.abort(grpc.StatusCode.NOT_FOUND, "Пост не найден")
        if post.is_private and post.user_id != request.user_id:
            context.abort(grpc.StatusCode.PERMISSION_DENIED, "Нет доступа к посту")
        db.close()
        kafka_producer.send_post_viewed_event(post.post_id, post.user_id)
        return post_service_pb2.viewPostResponse(
            post_id=post.post_id,
            title=post.title,
            description=post.description,
            user_id=post.user_id,
            create_time=str(post.create_time),
            last_update=str(post.last_update),
            is_private=post.is_private,
            tags=post.tags
        )
    
    def likePost(self, request, context):
        db = Session()

        post = db.query(Post).filter(
            Post.post_id == request.post_id,
            Post.deleted_at.is_(None)
        ).first()

        if not post:
            context.abort(grpc.StatusCode.NOT_FOUND, "Пост не найден")

        if post.is_private and post.user_id != request.user_id:
            context.abort(grpc.StatusCode.PERMISSION_DENIED, "Нет доступа к посту")

        like_exists = db.query(
            exists().where(
                Like.post_id == request.post_id,
                Like.user_id == request.user_id,
                Like.deleted_at.is_(None)
            )
        ).scalar()

        if like_exists:
            context.abort(grpc.StatusCode.ALREADY_EXISTS, "Лайк уже есть")

        new_like = Like(user_id=request.user_id, post_id=request.post_id)
        db.add(new_like)
        db.commit()

        db.refresh(new_like)

        kafka_producer.send_post_liked_event(new_like.post_id, new_like.user_id)

        return post_service_pb2.likePostResponse(
            like_id=new_like.like_id,
            user_id=new_like.user_id,
            post_id=new_like.post_id,
            created_at=str(new_like.created_at)
        )
    
    def commentPost(self, request, context):
        db = Session()

        post = db.query(Post).filter(
            Post.post_id == request.post_id,
            Post.deleted_at.is_(None)
        ).first()

        if not post:
            context.abort(grpc.StatusCode.NOT_FOUND, "Пост не найден")

        if post.is_private and post.user_id != request.user_id:
            context.abort(grpc.StatusCode.PERMISSION_DENIED, "Нет доступа к посту")

        comment = Comment(
            post_id=request.post_id,
            user_id=request.user_id,
            text=request.text
        )
        db.add(comment)
        db.commit()
        db.refresh(comment)

        if not comment:
            context.abort(grpc.StatusCode.NOT_FOUND, "Комментарий не был добавлен")

        kafka_producer.send_post_commented_event(comment.post_id, comment.user_id, comment.text)

        return post_service_pb2.commentPostResponse(
            comment_id=comment.comment_id,
            post_id=comment.post_id,
            user_id=comment.user_id,
            text=comment.text,
            created_at=str(comment.created_at)
        )
    

    def commentsListing(self, request, context):
        db = Session()

        post = db.query(Post).filter(
            Post.post_id == request.post_id,
            Post.deleted_at.is_(None)
        ).first()

        if not post:
            context.abort(grpc.StatusCode.NOT_FOUND, "Пост не найден")

        if post.is_private and post.user_id != request.user_id:
            context.abort(grpc.StatusCode.PERMISSION_DENIED, "Нет доступа к посту")

        comments = db.query(Comment).filter(
            Comment.post_id == request.post_id,
            Comment.deleted_at.is_(None)
        ).limit(request.limit).offset(request.offset).all()

        return post_service_pb2.commentsListingResponse(
            comments=[
                post_service_pb2.comment(
                    comment_id=c.comment_id,
                    post_id=c.post_id,
                    user_id=c.user_id,
                    text=c.text,
                    created_at=str(c.created_at)
                )
                for c in comments
            ]
        )
    def registerUser(self, request, context):
        db = Session()
        try:
            new_user = User(
                lastname=request.lastname,
                firstname=request.firstname,
                username=request.username,
                age=request.age,
                email=request.email,
                phone=request.phone,
                birthDay=request.birthDay
            )
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            
            kafka_producer.send_user_registered_event(
                user_id=new_user.user_id,
                registered_at=new_user.created_at
            )
            
            return post_service_pb2.userRegisterResponse(user_id=new_user.user_id, registered_at=new_user.created_at)
            
        except Exception as e:
            db.rollback()
            context.abort(grpc.StatusCode.INTERNAL, str(e))
        finally:
            db.close()
