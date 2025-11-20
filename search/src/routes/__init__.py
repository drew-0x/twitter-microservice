import logging
from os import stat

from fastapi import APIRouter, Depends, HTTPException

from src.dependencies.mq import produce_message

from sqlalchemy.exc import SQLAlchemyError

from src.grpc.client.user_service_pb2_grpc import User


from src.dependencies.auth import UserToken, VerifyToken


from src.dependencies.db import db_session as DB


router = APIRouter()
logger = logging.getLogger(__name__)
