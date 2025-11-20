from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class TweetStruct(_message.Message):
    __slots__ = ("id", "user_id", "content", "num_likes", "num_replys", "num_reposts", "created_at")
    ID_FIELD_NUMBER: _ClassVar[int]
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    NUM_LIKES_FIELD_NUMBER: _ClassVar[int]
    NUM_REPLYS_FIELD_NUMBER: _ClassVar[int]
    NUM_REPOSTS_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    id: str
    user_id: str
    content: str
    num_likes: int
    num_replys: int
    num_reposts: int
    created_at: int
    def __init__(self, id: _Optional[str] = ..., user_id: _Optional[str] = ..., content: _Optional[str] = ..., num_likes: _Optional[int] = ..., num_replys: _Optional[int] = ..., num_reposts: _Optional[int] = ..., created_at: _Optional[int] = ...) -> None: ...

class GetTweetsReq(_message.Message):
    __slots__ = ("tweet_ids",)
    TWEET_IDS_FIELD_NUMBER: _ClassVar[int]
    tweet_ids: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, tweet_ids: _Optional[_Iterable[str]] = ...) -> None: ...

class GetTweetsRes(_message.Message):
    __slots__ = ("tweets",)
    TWEETS_FIELD_NUMBER: _ClassVar[int]
    tweets: _containers.RepeatedCompositeFieldContainer[TweetStruct]
    def __init__(self, tweets: _Optional[_Iterable[_Union[TweetStruct, _Mapping]]] = ...) -> None: ...
