from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_content_plan_actions_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура после генерации контент-плана.
    Предлагает создать пост для первого дня.
    """
    buttons = [
        [
            InlineKeyboardButton(text="Создать пример поста 💻", callback_data="generate_example_post")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# get_post_generation_actions_keyboard удалена, так как не используется
