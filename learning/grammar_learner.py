from db.crud import get_node, create_node, get_or_create_node, create_path, get_paths_from


def init_grammar_patterns():
    """Initialize base grammar patterns in the database if not exists"""
    patterns = [
        ("question_word", ["what", "who", "where", "when", "why", "how"]),
        ("article", ["a", "an", "the"]),
        ("pronoun", ["me", "us", "him", "her", "them", "it", "you", "i"]),
        ("request_verb", ["tell", "show", "give", "explain", "describe", "find", "get"]),
        ("linking_verb", ["is", "are", "was", "were", "be"]),
        ("punctuation", ["?", ".", "!", ","]),
        ("preposition", ["of", "in", "on", "at", "to", "for", "with", "by"]),
    ]
    
    for word_type, words in patterns:
        for word in words:
            node = get_node(word)
            if not node:
                create_node(word, node_type=word_type)
            elif not node.type:
                node.type = word_type


def get_word_type(word):
    """Get word type from DB - fully algorithmic"""
    node = get_node(word.lower())
    if node and node.type:
        return node.type
    return None


def get_token_types(tokens):
    """Get types for all tokens from database"""
    return [(t, get_word_type(t.lower())) for t in tokens]


def detect_pattern(tokens):
    """Detect pattern using database node types - fully algorithmic"""
    tokens_lower = [t.lower() for t in tokens]
    
    pattern_key = " ".join(tokens_lower)
    learned = check_learned_pattern(pattern_key)
    if learned:
        return learned
    
    token_types = get_token_types(tokens_lower)
    types_only = [t[1] for t in token_types]
    
    has_question_word = types_only[0] == "question_word" if types_only else False
    has_linking_verb = "linking_verb" in types_only or "verb" in types_only
    has_preposition = "preposition" in types_only
    ends_with_question = types_only[-1] == "punctuation" and tokens_lower[-1] == "?" if types_only else False
    starts_with_linking = types_only[0] == "linking_verb" if types_only else False
    starts_with_request = types_only[0] == "request_verb" if types_only else False
    
    if tokens_lower[0] == "how" and "you" in tokens_lower and ends_with_question:
        return {
            "pattern": "how_are_you",
            "type": "self_state_query",
            "expects": "state"
        }
    
    if has_question_word and "think" in tokens_lower and "about" in tokens_lower and ends_with_question:
        about_idx = tokens_lower.index("about")
        topic_tokens = [t for t in tokens_lower[about_idx+1:-1] if t not in ["a", "an", "the"]]
        return {
            "pattern": "what_do_you_think_about_x",
            "type": "opinion_query",
            "topic": " ".join(topic_tokens),
            "expects": "opinion"
        }
    
    if has_question_word and has_linking_verb and has_preposition and ends_with_question:
        prep_idx = next((i for i, (t, ty) in enumerate(token_types) if ty == "preposition"), -1)
        if prep_idx > 2:
            property_tokens = [t for t, ty in token_types[2:prep_idx] if ty != "article"]
            entity_tokens = [t for t, ty in token_types[prep_idx+1:-1] if ty != "article"]
            return {
                "pattern": "question_word_verb_x_prep_y",
                "type": "property_of_query",
                "property": " ".join(property_tokens),
                "entity": " ".join(entity_tokens),
                "expects": "property_value"
            }
    
    if has_question_word and has_linking_verb and ends_with_question:
        subject_tokens = [t for t, ty in token_types[2:-1] if ty != "article"]
        subject = " ".join(subject_tokens)
        
        if len(token_types) >= 4 and token_types[2][0] in ["your", "my"]:
            possessive = token_types[2][0]
            property_tokens = [t for t, ty in token_types[3:-1] if ty != "article"]
            property_name = " ".join(property_tokens)
            
            return {
                "pattern": "question_word_verb_possessive_x",
                "type": "self_query" if possessive == "your" else "user_query",
                "possessive": possessive,
                "property": property_name,
                "expects": "self_property"
            }
        
        question_word = tokens_lower[0]
        question_node = get_node(question_word)
        expects = "definition"
        if question_node:
            paths = get_paths_from(question_word)
            for p in paths:
                if p.relation_type == "expects_answer_type" and p.to_node:
                    expects = p.to_node.connection_text
                    break
        
        return {
            "pattern": f"{question_word}_verb_x",
            "type": "definition_query" if question_word == "what" else f"{expects}_query",
            "subject": subject,
            "expects": expects,
            "question_word": question_word
        }
    
    if starts_with_request:
        verb = tokens_lower[0]
        remaining_tokens = token_types[1:]
        
        target = None
        if remaining_tokens and remaining_tokens[0][1] == "pronoun":
            target = remaining_tokens[0][0]
            remaining_tokens = remaining_tokens[1:]
        
        obj_tokens = [t for t, ty in remaining_tokens if ty not in ["article", "punctuation"]]
        if obj_tokens:
            return {
                "pattern": "request_verb_x",
                "type": "request",
                "verb": verb,
                "target": target,
                "object": " ".join(obj_tokens),
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
    
    inferred = infer_intent_from_graph(tokens_lower, token_types)
    if inferred:
        return inferred
    
    return None


def get_known_patterns():
    """Get all known grammar pattern structures from the database"""
    patterns = []
    
    patterns.append({
        "structure": ["X"],
        "name": "single word",
        "type": "greeting_or_command",
        "example": "hello"
    })
    patterns.append({
        "structure": ["question_word", "linking_verb", "X", "preposition", "Y", "punctuation"],
        "name": "what is X of Y?",
        "type": "property_of_query",
        "example": "what is the color of apple?"
    })
    patterns.append({
        "structure": ["question_word", "linking_verb", "X", "punctuation"],
        "name": "what is X?",
        "type": "definition_query",
        "example": "what is time?"
    })
    patterns.append({
        "structure": ["request_verb", "pronoun", "X"],
        "name": "tell me X",
        "type": "request",
        "example": "tell me the time"
    })
    patterns.append({
        "structure": ["linking_verb", "X", "Y", "punctuation"],
        "name": "is X Y?",
        "type": "property_query",
        "example": "is apple red?"
    })
    patterns.append({
        "structure": ["X", "linking_verb", "article", "Y"],
        "name": "X is a Y",
        "type": "definition_statement",
        "example": "apple is a fruit"
    })
    patterns.append({
        "structure": ["pronoun", "X", "preposition", "X", "article", "X"],
        "name": "I want to know X",
        "type": "indirect_question",
        "example": "I want to know the time"
    })
    
    return patterns


def match_to_known_patterns(token_types):
    """Find which known patterns the input is most similar to"""
    known = get_known_patterns()
    matches = []
    
    input_structure = [ty if ty else "X" for t, ty in token_types]
    
    for pattern in known:
        score = 0
        pattern_struct = pattern["structure"]
        
        if input_structure and pattern_struct:
            if input_structure[0] == pattern_struct[0]:
                score += 3
            if input_structure[-1] == pattern_struct[-1]:
                score += 2
        
        for ptype in pattern_struct:
            if ptype in input_structure:
                score += 1
        
        len_diff = abs(len(input_structure) - len(pattern_struct))
        score -= len_diff * 0.5
        
        if score > 0:
            matches.append((pattern, score))
    
    matches.sort(key=lambda x: x[1], reverse=True)
    return matches


def suggest_pattern_transformation(tokens, token_types):
    """Suggest how to transform input to match a known pattern"""
    matches = match_to_known_patterns(token_types)
    
    if not matches:
        return None
    
    best_match = matches[0][0]
    suggestions = []
    
    input_words = [t for t, ty in token_types if ty not in ["article", "punctuation"]]
    focus_word = input_words[-1] if input_words else ""
    
    if best_match["type"] == "definition_query":
        suggestions.append(f"what is {focus_word}?")
    elif best_match["type"] == "request":
        suggestions.append(f"tell me {' '.join(input_words[-2:]) if len(input_words) >= 2 else focus_word}")
    elif best_match["type"] == "property_of_query":
        if len(input_words) >= 2:
            suggestions.append(f"what is the {input_words[-2]} of {input_words[-1]}?")
    
    return {
        "closest_pattern": best_match,
        "suggestions": suggestions,
        "focus": focus_word,
        "all_matches": matches[:3]
    }


def infer_intent_from_graph(tokens, token_types):
    """Intelligently infer intent by traversing graph for each token"""
    from reasoning.graph_traversal import traverse_deep
    
    pattern_match = suggest_pattern_transformation(tokens, token_types)
    
    meaningful_tokens = [(t, ty) for t, ty in token_types 
                         if ty not in ["article", "pronoun", "punctuation", "preposition"]]
    
    if not meaningful_tokens:
        meaningful_tokens = [(t, ty) for t, ty in token_types if ty != "punctuation"]
    
    if not meaningful_tokens and tokens:
        meaningful_tokens = [(tokens[0], None)]
    
    intent_signals = {
        "question": 0,
        "request": 0,
        "statement": 0,
        "greeting": 0
    }
    related_concepts = {}
    key_definitions = {}
    
    question_indicators = ["want", "need", "know", "tell", "show", "find", "get"]
    greeting_indicators = ["hi", "hello", "hey", "greetings", "good", "morning", "evening", "afternoon"]
    
    for t, ty in token_types:
        if t in question_indicators:
            intent_signals["request"] += 2
        if t in greeting_indicators:
            intent_signals["greeting"] += 2
    
    for token, ttype in meaningful_tokens:
        node = get_node(token)
        if not node:
            intent_signals["statement"] += 1
            continue
            
        if node.type == "interjection" or "greeting" in (node.definition or "").lower():
            intent_signals["greeting"] += 2
            
        paths = get_paths_from(token)
        for p in paths:
            if p.to_node:
                rel = p.relation_type
                target = p.to_node.connection_text
                
                if token not in related_concepts:
                    related_concepts[token] = []
                related_concepts[token].append((rel, target, p.confidence))
                
                if rel == "definition":
                    key_definitions[token] = target
                    if "greeting" in target.lower() or "hello" in target.lower():
                        intent_signals["greeting"] += 2
                elif rel in ["is_a", "type_of"]:
                    intent_signals["question"] += 1
                elif rel in ["can", "does", "has"]:
                    intent_signals["request"] += 1
    
    primary_intent = max(intent_signals, key=intent_signals.get)
    
    focus_tokens = [t for t, ty in meaningful_tokens if ty in ["noun", "verb", None]]
    if not focus_tokens:
        focus_tokens = [t for t, _ in meaningful_tokens]
    
    if focus_tokens:
        focus_word = focus_tokens[-1] if focus_tokens else tokens[-1]
        
        clarifying_options = []
        if focus_word in related_concepts:
            for rel, target, conf in related_concepts[focus_word][:3]:
                clarifying_options.append(target)
        
        return {
            "pattern": "inferred_intent",
            "type": "inferred_query",
            "intent": primary_intent,
            "focus": focus_word,
            "tokens": tokens,
            "definitions": key_definitions,
            "related": related_concepts,
            "clarifying_options": clarifying_options,
            "pattern_match": pattern_match,
            "expects": "clarification"
        }
    
    if pattern_match:
        return {
            "pattern": "inferred_intent",
            "type": "inferred_query",
            "intent": "unknown",
            "focus": pattern_match.get("focus", ""),
            "tokens": tokens,
            "definitions": {},
            "related": {},
            "clarifying_options": [],
            "pattern_match": pattern_match,
            "expects": "clarification"
        }
    
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
    
    words = pattern_key.split()
    content_words = [w for w in words if w not in ['?', '.', '!', ',', 'a', 'an', 'the', 'i']]
    
    if len(content_words) == 1:
        semantic = find_pattern_via_semantic(content_words[0])
        if semantic:
            return semantic
    
    return None


def find_similar_pattern(pattern_key, max_depth=5, threshold=0.6):
    """Find similar patterns using deep graph traversal"""
    words = pattern_key.split()
    content_words = set(w.lower() for w in words if w not in ['?', '.', '!', ',', 'a', 'an', 'the', 'i'])
    
    if not content_words:
        return None
    
    from db.crud import get_node_by_id
    from db.models import Connection, get_session
    
    session = get_session()
    try:
        learned_patterns = session.query(Connection).filter(
            Connection.type == "learned_pattern"
        ).all()
        
        if not learned_patterns:
            return None
        
        best_match = None
        best_score = 0
        
        for lp in learned_patterns:
            lp_words = set(w.lower() for w in lp.connection_text.split() 
                          if w not in ['?', '.', '!', ',', 'a', 'an', 'the', 'i'])
            
            if not lp_words:
                continue
            
            shared_words = content_words & lp_words
            if len(shared_words) < 2:
                continue
            direct_score = len(shared_words) / max(len(content_words), len(lp_words)) if shared_words else 0
            
            deep_score = 0
            deep_matches = set()
            
            for word in content_words:
                visited = set()
                score, matches = _traverse_for_pattern(word, lp_words, max_depth, visited, 1.0)
                deep_score += score
                deep_matches.update(matches)
            
            deep_score = min(deep_score / len(content_words), 1.0) if content_words else 0
            
            total_score = max(direct_score, deep_score * 0.8)
            if shared_words:
                total_score = direct_score + (deep_score * 0.3)
            
            if total_score > best_score and total_score >= threshold:
                lp_paths = get_paths_from(lp.connection_text)
                response = None
                pattern_type = "learned"
                
                for p in lp_paths:
                    if p.relation_type == "responds_with":
                        resp_node = get_node_by_id(p.to_connection)
                        if resp_node:
                            response = resp_node.connection_text
                    elif p.relation_type == "pattern_type":
                        type_node = get_node_by_id(p.to_connection)
                        if type_node:
                            pattern_type = type_node.connection_text
                
                if response:
                    best_score = total_score
                    best_match = {
                        "pattern": "similar_pattern",
                        "type": "learned_response",
                        "pattern_key": lp.connection_text,
                        "response": response,
                        "response_type": pattern_type,
                        "learned": True,
                        "similarity_score": total_score,
                        "shared_words": list(shared_words),
                        "deep_matches": list(deep_matches),
                        "depth_searched": max_depth
                    }
        
        return best_match
    finally:
        session.close()


def _traverse_for_pattern(word, target_words, max_depth, visited, current_confidence):
    """Recursively traverse graph to find connections to target words"""
    if max_depth <= 0 or word in visited or current_confidence < 0.1:
        return 0, set()
    
    visited.add(word)
    
    if word in target_words:
        return current_confidence, {word}
    
    paths = get_paths_from(word)
    best_score = 0
    matches = set()
    
    for p in paths:
        if p.to_node:
            target = p.to_node.connection_text.lower()
            
            if p.relation_type == "semantically_related":
                new_confidence = current_confidence * 0.9
            else:
                new_confidence = current_confidence * p.confidence
            
            if target in target_words:
                if new_confidence > best_score:
                    best_score = new_confidence
                    matches.add(target)
            elif p.relation_type == "semantically_related":
                sem_paths = get_paths_from(target)
                for sp in sem_paths:
                    if sp.relation_type == "responds_with":
                        if new_confidence > best_score:
                            best_score = new_confidence
                            matches.add(target)
                            break
            else:
                deeper_score, deeper_matches = _traverse_for_pattern(
                    target, target_words, max_depth - 1, visited, new_confidence
                )
                if deeper_score > best_score:
                    best_score = deeper_score
                    matches.update(deeper_matches)
    
    return best_score, matches


def find_pattern_via_semantic(word):
    """Find learned patterns through semantic connections"""
    from db.crud import get_node_by_id
    
    paths = get_paths_from(word)
    for p in paths:
        if p.relation_type == "semantically_related" and p.to_node:
            related_word = p.to_node.connection_text.lower()
            related_paths = get_paths_from(related_word)
            
            for rp in related_paths:
                if rp.relation_type == "responds_with":
                    resp_node = get_node_by_id(rp.to_connection)
                    if resp_node:
                        type_paths = get_paths_from(related_word)
                        pattern_type = "learned"
                        for tp in type_paths:
                            if tp.relation_type == "pattern_type":
                                type_node = get_node_by_id(tp.to_connection)
                                if type_node:
                                    pattern_type = type_node.connection_text
                        
                        return {
                            "pattern": "semantic_pattern",
                            "type": "learned_response",
                            "pattern_key": related_word,
                            "response": resp_node.connection_text,
                            "response_type": pattern_type,
                            "learned": True,
                            "via_semantic": word,
                            "similarity_score": 0.85
                        }
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
