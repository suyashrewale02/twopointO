import re


def tokenize(text):
    text = text.strip()
    
    tokens = re.findall(r"[\w]+|[?.!,;:]", text)
    
    return tokens


def tokenize_with_positions(text):
    text = text.strip()
    tokens = []
    
    for match in re.finditer(r"[\w]+|[?.!,;:]", text):
        tokens.append({
            "text": match.group(),
            "start": match.start(),
            "end": match.end()
        })
    
    return tokens
