from sqlalchemy.ext.asyncio import AsyncAttrs, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import BigInteger, String, Text, func
from datetime import datetime

from config import DB_URL

engine = create_async_engine(DB_URL)
async_session = async_sessionmaker(engine, expire_on_commit=False)

class Base(AsyncAttrs, DeclarativeBase):
    pass

class UserPreference1(Base):
    __tablename__ = 'user_preference1'
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    created_time: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

class ContentPlanAnswers(Base):
    __tablename__ = 'content_plan_answers'
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)

    topic_audience: Mapped[str] = mapped_column(Text, nullable=True)
    goal: Mapped[str] = mapped_column(Text, nullable=True)
    frequency_format: Mapped[str] = mapped_column(Text, nullable=True)
    usp: Mapped[str] = mapped_column(Text, nullable=True)
    examples: Mapped[str] = mapped_column(Text, nullable=True)
    content_tone: Mapped[str] = mapped_column(Text, nullable=True)
    specific_topics: Mapped[str] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now(), nullable=False)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)