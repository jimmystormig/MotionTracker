from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

_engine = None
_session_factory = None


def init_engine(database_url: str):
    global _engine, _session_factory
    _engine = create_async_engine(database_url, echo=False, pool_pre_ping=True)
    _session_factory = async_sessionmaker(_engine, expire_on_commit=False, class_=AsyncSession)


def get_engine():
    return _engine


async def get_session() -> AsyncSession:
    async with _session_factory() as session:
        yield session


class Base(DeclarativeBase):
    pass
