from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.database.models import UserPreference1, ContentPlanAnswers, async_session

# ====== Работа с UserPreference1 ======
async def save_user_preference(tg_id: int, question: str, answer: str):
    try:
        async with async_session() as session:
            new_record = UserPreference1(tg_id=tg_id, question=question, answer=answer)
            session.add(new_record)
            await session.commit()
    except SQLAlchemyError as e:
        print(f"Ошибка при сохранении данных в UserPreference1: {e}")

async def get_user_preferences(tg_id: int):
    try:
        async with async_session() as session:
            result = await session.scalars(select(UserPreference1).where(UserPreference1.tg_id == tg_id))
            return result.all()
    except SQLAlchemyError as e:
        print(f"Ошибка при получении данных из UserPreference1: {e}")
        return []

# ====== Работа с ContentPlanAnswers ======
async def save_content_plan_answers(data: dict):
    tg_id = data.get("tg_id")
    if not tg_id:
        raise ValueError("tg_id не найден в данных")

    try:
        async with async_session() as session:
            async with session.begin():
                record = await session.scalar(
                    select(ContentPlanAnswers).where(ContentPlanAnswers.tg_id == tg_id)
                )

                if not record:
                    new_record = ContentPlanAnswers(**data)
                    session.add(new_record)
                else:
                    for key, value in data.items():
                        if hasattr(record, key) and value is not None:
                            setattr(record, key, value)
                await session.commit()
    except Exception as e:
        print(f"Ошибка при сохранении данных в ContentPlanAnswers: {e}")

async def get_content_plan_answers(tg_id: int):
    try:
        async with async_session() as session:
            result = await session.scalar(
                select(ContentPlanAnswers).where(ContentPlanAnswers.tg_id == tg_id)
            )
            return result
    except Exception as e:
        print(f"Ошибка при получении данных: {e}")
        return None