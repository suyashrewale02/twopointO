import re
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from db.crud import get_node, create_node, get_or_create_node, create_path

FREE_DICTIONARY_API = "https://api.dictionaryapi.dev/api/v2/entries/en"

WEAK_TYPES = {"article", "punctuation", "preposition", "conjunction", "pronoun"}
STRONG_TYPES = {"noun", "verb", "adjective", "adverb"}

STOP_WORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "must", "shall", "can", "to", "of", "in",
    "for", "on", "with", "at", "by", "from", "as", "into", "through",
    "during", "before", "after", "above", "below", "between", "under",
    "again", "further", "then", "once", "here", "there", "when", "where",
    "why", "how", "all", "each", "few", "more", "most", "other", "some",
    "such", "no", "nor", "not", "only", "own", "same", "so", "than",
    "too", "very", "just", "also", "now", "or", "and", "but", "if",
    "because", "until", "while", "although", "this", "that", "these",
    "those", "it", "its", "etc", "often", "usually", "sometimes", "always"
}

GRAMMAR_WORDS = {
    "what": {"type": "question_word", "definition": "Used to ask for information about something"},
    "is": {"type": "verb", "definition": "Third person singular present of 'be'; links subject to predicate"},
    "are": {"type": "verb", "definition": "Second person singular and plural present of 'be'"},
    "a": {"type": "article", "definition": "Used before singular nouns to refer to one unspecified thing"},
    "an": {"type": "article", "definition": "Used before singular nouns starting with a vowel sound"},
    "the": {"type": "article", "definition": "Used to refer to specific or known nouns"},
    "?": {"type": "punctuation", "definition": "Question mark; indicates a question"},
    ".": {"type": "punctuation", "definition": "Period; indicates end of sentence"},
    "!": {"type": "punctuation", "definition": "Exclamation mark; indicates emphasis or emotion"},
    ",": {"type": "punctuation", "definition": "Comma; separates clauses or items"},
    "who": {"type": "question_word", "definition": "Used to ask about a person"},
    "where": {"type": "question_word", "definition": "Used to ask about a place or location"},
    "when": {"type": "question_word", "definition": "Used to ask about time"},
    "why": {"type": "question_word", "definition": "Used to ask for a reason"},
    "how": {"type": "question_word", "definition": "Used to ask about manner or degree"},
    "yes": {"type": "boolean", "definition": "Affirmative response"},
    "no": {"type": "boolean", "definition": "Negative response"},
    "i": {"type": "pronoun", "definition": "First person singular subject pronoun"},
    "me": {"type": "pronoun", "definition": "First person singular object pronoun"},
    "my": {"type": "pronoun", "definition": "First person singular possessive"},
    "mine": {"type": "pronoun", "definition": "First person singular possessive (standalone)"},
    "you": {"type": "pronoun", "definition": "Second person pronoun"},
    "your": {"type": "pronoun", "definition": "Second person possessive"},
    "yours": {"type": "pronoun", "definition": "Second person possessive (standalone)"},
    "he": {"type": "pronoun", "definition": "Third person singular masculine subject"},
    "him": {"type": "pronoun", "definition": "Third person singular masculine object"},
    "his": {"type": "pronoun", "definition": "Third person singular masculine possessive"},
    "she": {"type": "pronoun", "definition": "Third person singular feminine subject"},
    "her": {"type": "pronoun", "definition": "Third person singular feminine possessive/object"},
    "hers": {"type": "pronoun", "definition": "Third person singular feminine possessive (standalone)"},
    "it": {"type": "pronoun", "definition": "Third person singular neuter pronoun"},
    "its": {"type": "pronoun", "definition": "Third person singular neuter possessive"},
    "we": {"type": "pronoun", "definition": "First person plural subject"},
    "us": {"type": "pronoun", "definition": "First person plural object"},
    "our": {"type": "pronoun", "definition": "First person plural possessive"},
    "ours": {"type": "pronoun", "definition": "First person plural possessive (standalone)"},
    "they": {"type": "pronoun", "definition": "Third person plural subject"},
    "them": {"type": "pronoun", "definition": "Third person plural object"},
    "their": {"type": "pronoun", "definition": "Third person plural possessive"},
    "theirs": {"type": "pronoun", "definition": "Third person plural possessive (standalone)"},
    "this": {"type": "pronoun", "definition": "Demonstrative pronoun for near things"},
    "that": {"type": "pronoun", "definition": "Demonstrative pronoun for far things"},
    "these": {"type": "pronoun", "definition": "Demonstrative pronoun for near plural things"},
    "those": {"type": "pronoun", "definition": "Demonstrative pronoun for far plural things"},
    "whats": {"type": "question_word", "definition": "Contraction of 'what is'"},
    "what's": {"type": "question_word", "definition": "Contraction of 'what is'"},
    "hows": {"type": "question_word", "definition": "Contraction of 'how is'"},
    "how's": {"type": "question_word", "definition": "Contraction of 'how is'"},
    "whos": {"type": "question_word", "definition": "Contraction of 'who is'"},
    "who's": {"type": "question_word", "definition": "Contraction of 'who is'"},
    "wheres": {"type": "question_word", "definition": "Contraction of 'where is'"},
    "where's": {"type": "question_word", "definition": "Contraction of 'where is'"},
    "thats": {"type": "pronoun", "definition": "Contraction of 'that is'"},
    "that's": {"type": "pronoun", "definition": "Contraction of 'that is'"},
    "its": {"type": "pronoun", "definition": "Contraction of 'it is' or possessive of 'it'"},
    "it's": {"type": "pronoun", "definition": "Contraction of 'it is'"},
    "im": {"type": "pronoun", "definition": "Contraction of 'I am'"},
    "i'm": {"type": "pronoun", "definition": "Contraction of 'I am'"},
    "youre": {"type": "pronoun", "definition": "Contraction of 'you are'"},
    "you're": {"type": "pronoun", "definition": "Contraction of 'you are'"},
    "dont": {"type": "verb", "definition": "Contraction of 'do not'"},
    "don't": {"type": "verb", "definition": "Contraction of 'do not'"},
    "cant": {"type": "verb", "definition": "Contraction of 'cannot'"},
    "can't": {"type": "verb", "definition": "Contraction of 'cannot'"},
    "wont": {"type": "verb", "definition": "Contraction of 'will not'"},
    "won't": {"type": "verb", "definition": "Contraction of 'will not'"},
    "isnt": {"type": "verb", "definition": "Contraction of 'is not'"},
    "isn't": {"type": "verb", "definition": "Contraction of 'is not'"},
    "arent": {"type": "verb", "definition": "Contraction of 'are not'"},
    "aren't": {"type": "verb", "definition": "Contraction of 'are not'"},
}


def find_semantically_related(word, definition_words, already_learned):
    """Find words in database that share semantic concepts with this word"""
    from db.models import Connection, get_session
    
    if not definition_words:
        return []
    
    key_concepts = set(w.lower() for w in definition_words[:5] if len(w) > 3)
    
    session = get_session()
    try:
        all_nodes = session.query(Connection).filter(
            Connection.definition.isnot(None)
        ).all()
        
        related = []
        for node in all_nodes:
            if node.connection_text.lower() == word.lower():
                continue
            if node.connection_text.lower() in already_learned:
                continue
            if not node.definition:
                continue
            
            node_def_words = set(extract_definition_words(node.definition))
            shared = key_concepts & node_def_words
            
            if len(shared) >= 1:
                score = len(shared) / max(len(key_concepts), len(node_def_words))
                if score >= 0.2 or len(shared) >= 2:
                    related.append((node.connection_text.lower(), list(shared), score))
        
        related.sort(key=lambda x: x[2], reverse=True)
        return [(r[0], r[1]) for r in related[:3]]
    finally:
        session.close()


def lookup_dictionary(word):
    word_lower = word.lower()
    
    if word_lower in GRAMMAR_WORDS:
        return {
            "word": word_lower,
            "type": GRAMMAR_WORDS[word_lower]["type"],
            "definition": GRAMMAR_WORDS[word_lower]["definition"]
        }
    
    url = f"{FREE_DICTIONARY_API}/{word_lower}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            result = {"word": word_lower, "definition": None, "type": None}
            
            if data and len(data) > 0:
                meanings = data[0].get("meanings", [])
                if meanings:
                    result["type"] = meanings[0].get("partOfSpeech", "").lower()
                    definitions = meanings[0].get("definitions", [])
                    if definitions:
                        result["definition"] = definitions[0].get("definition", None)
            
            return result
        return None
    except Exception:
        return None


def learn_word(word):
    word_lower = word.lower()
    
    existing = get_node(word_lower)
    if existing:
        return existing, False, "database"
    
    dict_data = lookup_dictionary(word_lower)
    
    if dict_data and dict_data.get("definition"):
        node = create_node(
            text=dict_data["word"],
            node_type=dict_data.get("type"),
            definition=dict_data.get("definition")
        )
        
        if dict_data.get("type"):
            type_node, _ = get_or_create_node(dict_data["type"], node_type="word_type")
            create_path(word_lower, "is_a", dict_data["type"])
        
        return node, True, "dictionary"
    
    return None, False, "not_found"


def learn_word_from_user(word, definition, word_type=None):
    word_lower = word.lower()
    node = create_node(text=word_lower, node_type=word_type, definition=definition)
    return node


def extract_definition_words(definition):
    if not definition:
        return []
    
    words = re.findall(r'[a-zA-Z]+', definition.lower())
    
    meaningful_words = [w for w in words if w not in STOP_WORDS and len(w) > 2]
    
    return meaningful_words


def get_connection_strength(from_type, to_type):
    if from_type in STRONG_TYPES and to_type in STRONG_TYPES:
        return 0.9
    elif from_type in STRONG_TYPES or to_type in STRONG_TYPES:
        return 0.7
    elif from_type in WEAK_TYPES or to_type in WEAK_TYPES:
        return 0.3
    else:
        return 0.5


def calculate_overlap_score(original_words, candidate_words):
    if not original_words or not candidate_words:
        return 0.0
    
    set_original = set(original_words)
    set_candidate = set(candidate_words)
    
    intersection = set_original & set_candidate
    union = set_original | set_candidate
    
    if not union:
        return 0.0
    
    return len(intersection) / len(union)


RELEVANCE_THRESHOLD = 0.1
MAX_WORKERS = 5


def fetch_word_data(word):
    """Fetch word data from DB or API - used for parallel processing"""
    word_lower = word.lower()
    
    existing = get_node(word_lower)
    if existing and existing.definition:
        return {
            "word": word_lower,
            "definition": existing.definition,
            "type": existing.type,
            "from_db": True,
            "node": existing
        }
    
    dict_data = lookup_dictionary(word_lower)
    if dict_data and dict_data.get("definition"):
        node = create_node(
            text=dict_data["word"],
            node_type=dict_data.get("type"),
            definition=dict_data.get("definition")
        )
        if dict_data.get("type"):
            get_or_create_node(dict_data["type"], node_type="word_type")
            create_path(word_lower, "is_a", dict_data["type"], update_if_higher=True)
        
        return {
            "word": word_lower,
            "definition": dict_data.get("definition"),
            "type": dict_data.get("type"),
            "from_db": False,
            "node": node
        }
    
    return {"word": word_lower, "definition": None, "type": None, "from_db": False, "node": None}


def fetch_words_parallel(words):
    """Fetch multiple words in parallel"""
    results = {}
    words_to_fetch = [w for w in words if w not in results]
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_word = {executor.submit(fetch_word_data, word): word for word in words_to_fetch}
        for future in as_completed(future_to_word):
            word = future_to_word[future]
            try:
                results[word] = future.result()
            except Exception as e:
                results[word] = {"word": word, "definition": None, "type": None, "from_db": False, "node": None}
    
    return results


def learn_word_deep(word, current_depth=0, max_depth=10, learned_words=None, all_connections=None, parent_def_words=None):
    if learned_words is None:
        learned_words = set()
    if all_connections is None:
        all_connections = []
    
    word_lower = word.lower()
    indent = "  " * current_depth
    
    if word_lower in learned_words:
        return get_node(word_lower), False, "already_learned", all_connections
    
    if current_depth >= max_depth:
        print(f"    {indent}[Depth {current_depth}] {word_lower} — MAX DEPTH REACHED")
        return get_node(word_lower), False, "max_depth", all_connections
    
    learned_words.add(word_lower)
    
    existing = get_node(word_lower)
    node_definition = None
    node_type = None
    from_db = False
    
    if existing and existing.definition:
        node_definition = existing.definition
        node_type = existing.type
        from_db = True
    else:
        dict_data = lookup_dictionary(word_lower)
        if dict_data and dict_data.get("definition"):
            node_definition = dict_data.get("definition")
            node_type = dict_data.get("type")
            
            existing = create_node(
                text=dict_data["word"],
                node_type=node_type,
                definition=node_definition
            )
            
            if node_type:
                get_or_create_node(node_type, node_type="word_type")
                create_path(word_lower, "is_a", node_type, update_if_higher=True)
    
    if not node_definition:
        print(f"    {indent}[Depth {current_depth}] {word_lower} — NOT FOUND")
        return None, False, "not_found", all_connections
    
    definition_words = extract_definition_words(node_definition)
    current_def_words = set(definition_words)
    
    if current_depth == 0:
        print(f"    {indent}[Depth {current_depth}] {word_lower} [{node_type or '?'}] {'(from DB)' if from_db else '(from API)'}")
        print(f"    {indent}  Definition: \"{node_definition[:80]}{'...' if len(node_definition) > 80 else ''}\"")
        print(f"    {indent}  Key words: {', '.join(definition_words[:5])}")
    
    words_to_learn = [w for w in definition_words[:3] if w != word_lower and w not in learned_words]
    
    semantic_related = find_semantically_related(word_lower, definition_words, learned_words)
    for related_word, shared_concepts in semantic_related:
        create_path(word_lower, "semantically_related", related_word, confidence=0.85, update_if_higher=True)
        create_path(related_word, "semantically_related", word_lower, confidence=0.85, update_if_higher=True)
        all_connections.append({
            "from": word_lower,
            "to": related_word,
            "strength": 0.85,
            "depth": current_depth,
            "type": "semantic",
            "shared": shared_concepts
        })
        if current_depth == 0:
            print(f"    {indent}  ⟷ {related_word} (semantic match via: {', '.join(shared_concepts[:3])})")
    
    if words_to_learn:
        print(f"    {indent}  Fetching {len(words_to_learn)} words in parallel...")
        word_data = fetch_words_parallel(words_to_learn)
        
        children_to_expand = []
        
        for def_word in words_to_learn:
            data = word_data.get(def_word, {})
            def_definition = data.get("definition")
            def_type = data.get("type")
            def_node = data.get("node")
            
            if not def_node or not def_definition:
                continue
            
            learned_words.add(def_word)
            
            def_words_of_candidate = extract_definition_words(def_definition)
            
            from_type = node_type or "unknown"
            to_type = def_type or "unknown"
            type_strength = get_connection_strength(from_type, to_type)
            
            if parent_def_words:
                overlap = calculate_overlap_score(parent_def_words, set(def_words_of_candidate))
                strength = min(0.95, type_strength * (1 + overlap))
                shared = parent_def_words & set(def_words_of_candidate)
                if shared:
                    print(f"    {indent}  ├─ {def_word} [{def_type or '?'}] ({int(strength*100)}%) [shared: {list(shared)[:3]}]")
                else:
                    print(f"    {indent}  ├─ {def_word} [{def_type or '?'}] ({int(strength*100)}%)")
            else:
                strength = type_strength
                print(f"    {indent}  ├─ {def_word} [{def_type or '?'}] ({int(strength*100)}%)")
            
            print(f"    {indent}  │  \"{def_definition[:50]}{'...' if len(def_definition) > 50 else ''}\"")
            
            create_path(word_lower, "related_to", def_word, confidence=strength, update_if_higher=True)
            all_connections.append({
                "from": word_lower,
                "to": def_word,
                "strength": strength,
                "depth": current_depth,
                "definition": def_definition[:60] + "..." if len(def_definition) > 60 else def_definition
            })
            
            children_to_expand.append((def_word, current_def_words))
        
        for child_word, child_parent_words in children_to_expand:
            learn_word_deep(child_word, current_depth + 1, max_depth, learned_words, all_connections, child_parent_words)
    
    return existing, not from_db, "database" if from_db else "dictionary", all_connections
