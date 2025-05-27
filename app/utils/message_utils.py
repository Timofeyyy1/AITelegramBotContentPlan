import re

def split_text(text: str, max_length: int = 4096) -> list[str]:

    if not text:
        return []
    
    parts = []
    current_start = 0

    while current_start < len(text):
        chunk = text[current_start:]

        # Если оставшийся текст меньше или равен максимальной длине, добавляем его и выходим
        if len(chunk) <= max_length:
            parts.append(chunk)
            break

        search_start_offset = int(max_length * 0.8)
        search_end_offset = max_length
        
        # Индекс для разрыва в тексте `chunk`
        split_point_in_chunk = -1

        for i in range(search_end_offset - 1, search_start_offset -1, -1):
            if i < 0: # Не уходим за начало chunk
                continue

            char = chunk[i]
            
            # Приоритет 1: Двойной перенос строки
            if char == '\n' and i > 0 and chunk[i-1] == '\n':
 
                temp_chunk = chunk[:i-1] # Проверяем текст до потенциального \n\n
                if not has_unclosed_markdown(temp_chunk):
                    split_point_in_chunk = i + 1 # +1, чтобы включить '\n\n'
                    break

            # Приоритет 2: Одинарный перенос строки
            elif char == '\n':
                temp_chunk = chunk[:i]
                if not has_unclosed_markdown(temp_chunk):
                    split_point_in_chunk = i + 1 # +1, чтобы включить '\n'
                    break
            
            # Приоритет 3: Пробел
            elif char == ' ':
                temp_chunk = chunk[:i]
                if not has_unclosed_markdown(temp_chunk):
                    split_point_in_chunk = i + 1 # +1, чтобы включить ' '
                    break
        
        # Если нашли безопасную точку разрыва, используем её
        if split_point_in_chunk != -1:
            parts.append(chunk[:split_point_in_chunk])
            current_start += split_point_in_chunk
        else:
            
            # Попробуем найти последний перенос строки или пробел до max_length
            last_newline = chunk.rfind('\n', 0, max_length)
            last_space = chunk.rfind(' ', 0, max_length)
            
            if last_newline != -1:
                split_point_in_chunk = last_newline + 1
            elif last_space != -1:
                split_point_in_chunk = last_space + 1
            else:
                # Если и так не смогли, просто обрезаем.
                
                split_point_in_chunk = max_length 

            parts.append(chunk[:split_point_in_chunk])
            current_start += split_point_in_chunk

    return parts

def has_unclosed_markdown(text: str) -> bool:

    bold_count = text.count('**')
    if bold_count % 2 != 0:
        return True # Есть незакрытый **
    
    # Считаем баланс тегов
    balance_bold = 0
    balance_italic = 0
    i = 0
    while i < len(text):
        if text[i:i+2] == '**':
            if balance_bold == 0: 
                balance_bold += 1
            else: 
                balance_bold -= 1
            i += 2
        elif text[i] == '_':

            if (i == 0 or not text[i-1].isalnum()) and \
               (i == len(text) - 1 or not text[i+1].isalnum()):
                if balance_italic == 0:
                    balance_italic += 1
                else:
                    balance_italic -= 1
            i += 1
        else:
            i += 1
            
    return balance_bold != 0 or balance_italic != 0