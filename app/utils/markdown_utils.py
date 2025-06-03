import re
import logging

logger = logging.getLogger(__name__)

def escape_markdown_v2(text: str) -> str:
    """
    Экранирует специальные символы MarkdownV2 для Telegram.
    Корректно обрабатывает парные и непарные теги (**, _),
    предотвращая ошибки Telegram.
    """
    processed_chunks = []
    open_tags_stack = []

    i = 0
    while i < len(text):
        if text[i:i+2] == '**':
            if not open_tags_stack or open_tags_stack[-1][0] != '**':
                open_tags_stack.append(('**', len(processed_chunks)))
                processed_chunks.append('**')
            else:
                open_tags_stack.pop()
                processed_chunks.append('**')
            i += 2
        elif text[i] == '_':
            is_word_char_before = (i > 0 and text[i-1].isalnum())
            is_word_char_after = (i < len(text) - 1 and text[i+1].isalnum())

            if is_word_char_before or is_word_char_after:
                processed_chunks.append('\\_')
            elif not open_tags_stack or open_tags_stack[-1][0] != '_':
                open_tags_stack.append(('_', len(processed_chunks)))
                processed_chunks.append('_')
            else:
                open_tags_stack.pop()
                processed_chunks.append('_')
            i += 1
        elif text[i] in r'\[]()~`>#+-=|{}.!':
            processed_chunks.append('\\' + text[i])
            i += 1
        else:
            processed_chunks.append(text[i])
            i += 1
    
    for tag_type, chunk_index in open_tags_stack:
        logger.warning(f"Found unclosed tag '{tag_type}'. Escaping it at processed_chunks index {chunk_index}.")
        if tag_type == '**':
            processed_chunks[chunk_index] = '\\*\\*'
        elif tag_type == '_':
            processed_chunks[chunk_index] = '\\_'

    return "".join(processed_chunks)
