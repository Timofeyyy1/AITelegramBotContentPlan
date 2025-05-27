import re

def escape_markdown_v2(text: str) -> str:
    
    # Символы, которые нужно экранировать. Исключены '*' и '_',
    # так как они предполагаются используемыми для форматирования в format_content.
    chars_to_escape = r'\[]()~`>#+-=|{}.!' 
    
    # Регулярное выражение для экранирования символов
    escaped_text = re.sub(f'([{re.escape(chars_to_escape)}])', r'\\\1', text)
    
    return escaped_text