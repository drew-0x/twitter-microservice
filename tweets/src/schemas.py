from pydantic import BaseModel


# Tweet Schemas
class CreateTweetRequest(BaseModel):
    content: str


class UpdateTweetRequest(BaseModel):
    content: str


# Reply Schemas
class CreateReplyRequest(BaseModel):
    parent_id: str
    content: str
