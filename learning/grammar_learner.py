from db.crud import get_node, create_node, get_or_create_node, create_path, get_paths_from

QUESTION_WORDS = {
    "what": "thing",
    "who": "person",
    "where": "location",
    "when": "time",
    "why": "reason",
    "how": "manner"
}

REQUEST_VERBS = {"tell", "show", "give", "explain", "describe", "find", "get"}
ARTICLES = {"a", "an", "the"}
PRONOUNS = {"me", "us", "him", "her", "them", "it"}


def get_word_type(word):
    """Get word type from DB or return None"""
    node = get_node(word.lower())
    if node:
        return node.type
    return None


def detect_pattern(tokens):
    tokens_lower = [t.lower() for t in tokens]
    
    pattern_key = " ".join(tokens_lower)
    learned = check_learned_pattern(pattern_key)
    if learned:
        return learned
    
    if len(tokens_lower) >= 4 and tokens_lower[0] == "what" and tokens_lower[1] == "is" and tokens_lower[-1] == "?":
        subject_tokens = tokens_lower[2:-1]
        if subject_tokens and subject_tokens[0] in ARTICLES:
            subject_tokens = subject_tokens[1:]
        subject = " ".join(subject_tokens)
        return {
            "pattern": "what_is_x",
            "type": "definition_query",
            "subject": subject,
            "expects": "definition"
        }
    
    if len(tokens_lower) >= 3 and tokens_lower[0] in QUESTION_WORDS and tokens_lower[1] == "is" and tokens_lower[-1] == "?":
        question_type = QUESTION_WORDS[tokens_lower[0]]
        subject_tokens = tokens_lower[2:-1]
        if subject_tokens and subject_tokens[0] in ARTICLES:
            subject_tokens = subject_tokens[1:]
        subject = " ".join(subject_tokens)
        return {
            "pattern": f"{tokens_lower[0]}_is_x",
            "type": f"{question_type}_query",
            "subject": subject,
            "expects": question_type,
            "question_word": tokens_lower[0]
        }
    
    if len(tokens_lower) >= 3 and tokens_lower[0] in REQUEST_VERBS:
        verb = tokens_lower[0]
        remaining = tokens_lower[1:]
        
        target = None
        if remaining and remaining[0] in PRONOUNS:
            target = remaining[0]
            remaining = remaining[1:]
        
        if remaining and remaining[0] in ARTICLES:
            remaining = remaining[1:]
        
        if remaining:
            obj = " ".join(remaining)
            return {
                "pattern": f"{verb}_request",
                "type": "request",
                "verb": verb,
                "target": target,
                "object": obj,
                "expects": "action"
            }
    
    if len(tokens_lower) >= 4 and tokens_lower[0] == "is" and tokens_lower[-1] == "?":
        subject = tokens_lower[1]
        property_word = " ".join(tokens_lower[2:-1])
        return {
            "pattern": "is_x_y",
            "type": "property_query",
            "subject": subject,
            "property": property_word,
            "expects": "boolean"
        }
    
    if "is" in tokens_lower and "a" in tokens_lower:
        is_idx = tokens_lower.index("is")
        if is_idx > 0 and is_idx + 2 < len(tokens_lower) and tokens_lower[is_idx + 1] == "a":
            subject = " ".join(tokens_lower[:is_idx])
            obj = " ".join(tokens_lower[is_idx + 2:]).rstrip(".")
            return {
                "pattern": "x_is_a_y",
                "type": "definition_statement",
                "subject": subject,
                "object": obj,
                "creates": "is_a"
            }
    
    if "is" in tokens_lower:
        is_idx = tokens_lower.index("is")
        if is_idx > 0 and is_idx + 1 < len(tokens_lower):
            subject = " ".join(tokens_lower[:is_idx])
            predicate = " ".join(tokens_lower[is_idx + 1:]).rstrip(".")
            return {
                "pattern": "x_is_y",
                "type": "property_statement",
                "subject": subject,
                "predicate": predicate,
                "creates": "is"
            }
    
    pattern = try_dynamic_pattern(tokens_lower)
    if pattern:
        return pattern
    
    return None


def try_dynamic_pattern(tokens):
    """Try to build pattern dynamically from word types in DB"""
    if len(tokens) < 2:
        return None
    
    pattern_key = " ".join(tokens)
    learned = check_learned_pattern(pattern_key)
    if learned:
        return learned
    
    types = []
    for t in tokens:
        word_type = get_word_type(t)
        types.append((t, word_type))
    
    if types[0][1] == "verb" and len(tokens) >= 2:
        verb = types[0][0]
        
        remaining_start = 1
        target = None
        if len(types) > 1 and types[1][1] == "pronoun":
            target = types[1][0]
            remaining_start = 2
        
        obj_tokens = [t[0] for t in types[remaining_start:] if t[0] not in ARTICLES]
        if obj_tokens:
            return {
                "pattern": f"{verb}_dynamic",
                "type": "request",
                "verb": verb,
                "target": target,
                "object": " ".join(obj_tokens),
                "expects": "action",
                "learned": True
            }
    
    return None


def check_learned_pattern(pattern_key):
    """Check if this exact pattern was learned before, or find similar patterns"""
    node = get_node(pattern_key)
    if node and node.type == "learned_pattern":
        paths = get_paths_from(pattern_key)
        response = None
        pattern_type = "learned"
        
        for path in paths:
            from db.crud import get_node_by_id
            to_node = get_node_by_id(path.to_connection)
            if to_node:
                if path.relation_type == "responds_with":
                    response = to_node.connection_text
                elif path.relation_type == "pattern_type":
                    pattern_type = to_node.connection_text
        
        if response:
            return {
                "pattern": "learned_pattern",
                "type": "learned_response",
                "pattern_key": pattern_key,
                "response": response,
                "response_type": pattern_type,
                "learned": True
            }
    
    similar = find_similar_pattern(pattern_key)
    if similar:
        return similar
    
    return None


def find_similar_pattern(pattern_key):
    """Find similar patterns by checking shared words"""
    words = pattern_key.split()
    content_words = [w for w in words if w not in ['?', '.', '!', ',', 'a', 'an', 'the']]
    
    if not content_words:
        return None
    
    from db.crud import get_node_by_id
    
    for word in content_words:
        word_node = get_node(word)
        if not word_node:
            continue
        
        paths = get_paths_from(word)
        for path in paths:
            if path.relation_type == "used_in_pattern":
                to_node = get_node_by_id(path.to_connection)
                if to_node:
                    pattern_type = to_node.connection_text
                    
                    from db.models import Connection, Path, get_session
                    session = get_session()
                    try:
                        learned_patterns = session.query(Connection).filter(
                            Connection.type == "learned_pattern"
                        ).all()
                        
                        for lp in learned_patterns:
                            lp_paths = get_paths_from(lp.connection_text)
                            has_word = any(p.relation_type == "contains_word" and 
                                          get_node_by_id(p.to_connection) and 
                                          get_node_by_id(p.to_connection).connection_text == word 
                                          for p in lp_paths)
                            
                            if has_word:
                                for p in lp_paths:
                                    if p.relation_type == "responds_with":
                                        resp_node = get_node_by_id(p.to_connection)
                                        if resp_node:
                                            return {
                                                "pattern": "similar_pattern",
                                                "type": "learned_response",
                                                "pattern_key": lp.connection_text,
                                                "response": resp_node.connection_text,
                                                "response_type": pattern_type,
                                                "learned": True,
                                                "matched_word": word
                                            }
                    finally:
                        session.close()
    
    return None


def learn_grammar_pattern(pattern_name, pattern_tokens, pattern_type, expects=None):
    pattern_node, created = get_or_create_node(
        pattern_name,
        node_type="grammar_pattern",
        definition=f"Pattern: {' '.join(pattern_tokens)}"
    )
    
    if expects:
        expects_node, _ = get_or_create_node(expects, node_type="response_type")
        create_path(pattern_name, "expects", expects)
    
    return pattern_node, created
