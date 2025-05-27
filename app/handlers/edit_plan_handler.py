from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from app.handlers.content_plan_handlers import FSMContentPlan, QUESTIONS
from app.database.requests import get_content_plan_answers

router = Router()

@router.message(F.text == "🔄 Изменить план")
async def start_edit_plan(message: Message, state: FSMContext):
    plan_data = await get_content_plan_answers(message.from_user.id)

    if not plan_data:
        await message.answer("❌ У вас ещё нет сохранённого плана.")
        return

    # Получаем все состояния
    states = list(FSMContentPlan)

    keys = [
        "topic_audience",
        "goal",
        "frequency_format",
        "usp",
        "examples",
        "content_tone",
        "specific_topics"
    ]

    for i, key_name in enumerate(keys):
        value = getattr(plan_data, key_name)
        if value:
            await state.update_data(**{key_name: value})
            await state.set_state(states[i])  # используем состояние из списка
            await message.answer(QUESTIONS[i])
            break