import re

def tokenize(query):
    """Split query into words/tokens, removing punctuation."""
    words = re.findall(r'[a-zA-Z0-9]+', query)
    tokens = [word.lower() for word in words]
    return tokens
