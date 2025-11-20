from sqlalchemy import INT, Column, UUID, DateTime, String, false, func

from src.dependencies.db import Base

from uuid import uuid4


class Tweet(Base):
    __tablename__ = "tweets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    content = Column(String, nullable=False)
    num_likes = Column(INT, default=0)
    num_replys = Column(INT, default=0)
    num_reposts = Column(INT, default=0)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    def __init__(self, user_id, content) -> None:
        self.user_id = user_id
        self.content = content

    def to_dict(self):
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "content": self.content,
            "num_likes": self.num_likes,
            "num_replys": self.num_replys,
            "num_reposts": self.num_reposts,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def increment_likes(self, count=1):
        self.num_likes += count
        return self.num_likes

    def increment_replys(self, count=1):
        self.num_replys += count
        return self.num_replys

    def increment_reposts(self, count=1):
        self.num_reposts += count
        return self.num_reposts

    def decrement_likes(self, count=1):
        self.num_likes -= count
        return self.num_likes

    def decrement_replys(self, count=1):
        self.num_replys -= count
        return self.num_replys

    def decrement_reposts(self, count=1):
        self.num_reposts -= count
        return self.num_reposts


class ReplyTweet(Base):
    __tablename__ = "reply_tweets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    parent_id = Column(UUID(as_uuid=True), nullable=False)
    content = Column(String, nullable=False)
    num_likes = Column(INT, default=0)
    num_replys = Column(INT, default=0)
    num_reposts = Column(INT, default=0)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    def __init__(self, user_id, parent_id, content) -> None:
        self.user_id = user_id
        self.parent_id = parent_id
        self.content = content

    def to_dict(self):
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "parent_id": str(self.parent_id),
            "content": self.content,
            "num_likes": self.num_likes,
            "num_replys": self.num_replys,
            "num_reposts": self.num_reposts,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def increment_likes(self, count=1):
        self.num_likes += count
        return self.num_likes

    def increment_replys(self, count=1):
        self.num_replys += count
        return self.num_replys

    def increment_reposts(self, count=1):
        self.num_reposts += count
        return self.num_reposts


class TweetLike(Base):
    __tablename__ = "tweet_like"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    tweet_id = Column(UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    def __init__(self, user_id, tweet_id) -> None:
        self.user_id = user_id
        self.tweet_id = tweet_id

    def to_dict(self):
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "tweet_id": str(self.tweet_id),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class TweetRepost(Base):
    __tablename__ = "tweet_repost"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    tweet_id = Column(UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    def __init__(self, user_id, tweet_id) -> None:
        self.user_id = user_id
        self.tweet_id = tweet_id

    def to_dict(self):
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "tweet_id": str(self.tweet_id),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
