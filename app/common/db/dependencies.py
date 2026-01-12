from typing import AsyncGenerator
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession


async def get_db(request: Request) -> AsyncGenerator[AsyncSession, None]:
    sessionmaker = request.app.state.db_sessionmaker

    async with sessionmaker() as session:
        try:
            yield session
        finally:
            await session.close()
