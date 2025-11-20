from pydantic import BaseModel


# User Schemas
class CreateUserRequest(BaseModel):
    username: str
    password: str
    email: str


class LoginUserRequest(BaseModel):
    email: str
    password: str


# Follower Schemas
class CreateFollowerRequset(BaseModel):
    following_id: str
