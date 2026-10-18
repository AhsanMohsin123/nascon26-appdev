from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text
from app.config import settings

engine = create_async_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=40,
)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def init_db():
    async with engine.begin() as conn:
        from app.models import sport, league, match_event
        from app.models import roster as roster_model
        from app.models import store as store_model
        from app.models import user as user_model
        from app.models import streaming as streaming_model
        await conn.run_sync(Base.metadata.create_all)

    # Seed baseline data on startup if DB is empty
    async with AsyncSessionLocal() as session:
        r = await session.execute(text("SELECT COUNT(*) FROM sports"))
        count = r.scalar()
        if count == 0:
            from app.domain.seed import reset_and_seed
            await reset_and_seed(session, 42, {"var-jersey-001-M": 1, "var-jersey-001-L": 5})


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
