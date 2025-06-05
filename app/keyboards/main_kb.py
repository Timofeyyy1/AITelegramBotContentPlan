from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_content_plan_actions_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(text="Создать пример поста 💻", callback_data="generate_example_post")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

