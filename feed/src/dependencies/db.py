from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker, declarative_base, scoped_session

from src.dependencies.config import Config

config = Config()

url = URL.create(
    drivername="postgresql",
    username=config["DB_USERNAME"],
    database=config["DB_DATABASE"],
    host=config["DB_HOST"],
    port=int(str(config["DB_PORT"])),
    password=config["DB_PASSWORD"],
)

engine = create_engine(url)
db_session = scoped_session(
    sessionmaker(autocommit=False, autoflush=False, bind=engine)
)

Base = declarative_base()
Base.query = db_session.query_property()


def init_db():
    import src.models

    Base.metadata.create_all(bind=engine)
