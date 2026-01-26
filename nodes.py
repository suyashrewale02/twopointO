import requests
from db import Connection, get_session

FREE_DICTIONARY_API = "https://api.dictionaryapi.dev/api/v2/entries/en"


def lookup_word_from_dictionary(word):
    url = f"{FREE_DICTIONARY_API}/{word.lower()}"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            result = {"word": word.lower(), "definition": None, "type": None}
            
            if data and len(data) > 0:
                meanings = data[0].get("meanings", [])
                if meanings:
                    result["type"] = meanings[0].get("partOfSpeech", "").lower()
                    
                    definitions = meanings[0].get("definitions", [])
                    if definitions:
                        result["definition"] = definitions[0].get("definition", None)
            
            return result
        else:
            return None
    except Exception:
        return None


def get_node_by_text(text):
    session = get_session()
    try:
        node = session.query(Connection).filter(Connection.connection_text == text.lower()).first()
        return node
    finally:
        session.close()


def create_node(text, node_type=None, definition=None):
    session = get_session()
    try:
        existing = session.query(Connection).filter(Connection.connection_text == text.lower()).first()
        if existing:
            return existing
        node = Connection(
            connection_text=text.lower(),
            type=node_type,
            definition=definition
        )
        session.add(node)
        session.commit()
        session.refresh(node)
        return node
    finally:
        session.close()


def get_or_create_node(text, node_type=None):
    node = get_node_by_text(text)
    if node:
        return node
    return create_node(text, node_type=node_type)


def lookup_and_create_node(word):
    existing = get_node_by_text(word)
    if existing:
        return existing, False
    
    dict_data = lookup_word_from_dictionary(word)
    
    if dict_data and dict_data.get("definition"):
        node = create_node(
            text=dict_data["word"],
            node_type=dict_data.get("type"),
            definition=dict_data.get("definition")
        )
        return node, True
    
    return None, False
