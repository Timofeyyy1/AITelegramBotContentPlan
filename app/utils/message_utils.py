import re

def split_text(text: str, max_length: int = 4096) -> list[str]:
   
    if not text:
        return []
    
    parts = []
    current_start = 0

    while current_start < len(text):
        chunk_to_process = text[current_start:]

        if len(chunk_to_process) <= max_length:
            parts.append(chunk_to_process)
            break

        ideal_split_search_start = max(0, max_length - 500) 
        
        split_point_in_chunk = -1

        for m in re.finditer(r'\n\n', chunk_to_process[:max_length]):
            if m.start() >= ideal_split_search_start:
                if not re.match(r'[\*_\[\]\(\)~`>#+\-|=\{\}\.!]', chunk_to_process[m.end():].strip()):
                    split_point_in_chunk = m.end() 
                    break 

        if split_point_in_chunk == -1:
            for m in re.finditer(r'\n', chunk_to_process[:max_length]):
                if m.start() >= ideal_split_search_start:
                    if not re.match(r'[\*_\[\]\(\)~`>#+\-|=\{\}\.!]', chunk_to_process[m.end():].strip()): # Corrected typo: chunk_to_to_process -> chunk_to_process
                        split_point_in_chunk = m.end()
                        break

        if split_point_in_chunk == -1:
            for m in re.finditer(r'\s', chunk_to_process[:max_length]):
                if m.start() >= ideal_split_search_start:
                    if not re.match(r'[\*_\[\]\(\)~`>#+\-|=\{\}\.!]', chunk_to_process[m.end():].strip()):
                        split_point_in_chunk = m.end() 
                        break
        
        if split_point_in_chunk == -1:
            last_newline = chunk_to_process.rfind('\n', 0, max_length)
            last_space = chunk_to_process.rfind(' ', 0, max_length)

            if last_newline != -1:
                split_point_in_chunk = last_newline + 1
            elif last_space != -1:
                split_point_in_chunk = last_space + 1
            else:
                split_point_in_chunk = max_length 

        parts.append(chunk_to_process[:split_point_in_chunk])
        current_start += split_point_in_chunk

    return parts
