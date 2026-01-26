from db.crud import get_node


def ask_clarifying_question(subject):
    """Instead of saying 'I don't know', reason through the words and ask relevant questions"""
    words = subject.split()
    
    if len(words) == 1:
        return reason_about_word(subject)
    
    known_words = []
    all_related_concepts = set()
    
    for word in words:
        node = get_node(word)
        if node and node.definition:
            known_words.append((word, node.definition))
            concepts = extract_concepts_from_definition(node.definition)
            all_related_concepts.update(concepts)
    
    if not known_words:
        return f"I don't know any of these words: {', '.join(words)}. Can you teach me?"
    
    lines = [f"Let me think about '{subject}'..."]
    lines.append(f"\nWhat I know:")
    for word, defn in known_words[:3]:
        lines.append(f"  • {word}: {defn[:60]}...")
    
    useful_concepts = find_useful_concepts(all_related_concepts, subject)
    
    if useful_concepts:
        question = generate_helpful_question(useful_concepts, subject)
        lines.append(f"\n{question}")
    else:
        lines.append(f"\nI'm trying to understand '{subject}'. Can you help me?")
        lines.append(f"What specifically do you want to know about it?")
    
    return "\n".join(lines)


def extract_concepts_from_definition(definition):
    """Extract meaningful concepts from a definition"""
    if not definition:
        return set()
    
    stop_words = {'a', 'an', 'the', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
                  'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
                  'should', 'may', 'might', 'must', 'shall', 'can', 'need', 'dare',
                  'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from', 'as',
                  'or', 'and', 'but', 'if', 'then', 'than', 'so', 'that', 'this',
                  'it', 'its', 'which', 'who', 'whom', 'whose', 'what', 'where', 'when'}
    
    import re
    words = re.findall(r'\b[a-zA-Z]{3,}\b', definition.lower())
    return {w for w in words if w not in stop_words}


def find_useful_concepts(concepts, subject):
    """Find concepts that could help answer the question - uses graph relationships"""
    from db.crud import get_paths_from
    
    subject_words = subject.lower().split()
    related_from_graph = set()
    
    for word in subject_words:
        paths = get_paths_from(word)
        for p in paths:
            if p.to_node:
                related_from_graph.add(p.to_node.connection_text)
    
    if related_from_graph:
        matches = [c for c in concepts if c in related_from_graph]
        if matches:
            return matches
    
    concrete_concepts = []
    for concept in concepts:
        node = get_node(concept)
        if node and node.type in ['noun', 'verb']:
            concrete_concepts.append(concept)
    
    return concrete_concepts[:3]


def generate_helpful_question(concepts, subject):
    """Generate a helpful question based on found concepts - no hardcoded subjects"""
    if not concepts:
        return f"Can you tell me more about what you mean by '{subject}'?"
    
    if len(concepts) >= 2:
        return f"Are you asking about {concepts[0]} or {concepts[1]}?"
    
    concept = concepts[0]
    return f"I found '{concept}' might be related. Does this help answer your question about '{subject}'? (yes/no)"


def reason_about_word(word):
    """Deep reason about a single word"""
    node = get_node(word)
    if node and node.definition:
        concepts = extract_concepts_from_definition(node.definition)
        lines = [f"I know '{word}' means: {node.definition}"]
        
        if concepts:
            useful = list(concepts)[:5]
            lines.append(f"\nRelated concepts I could explore: {', '.join(useful)}")
            lines.append(f"\nWhat aspect of '{word}' would you like to know more about?")
        
        return "\n".join(lines)
    
    return f"I don't know '{word}' yet. Can you teach me?\nWhat is the definition of '{word}'?"


def build_answer(pattern_info, paths, node=None):
    if not pattern_info:
        return "I don't understand the question."
    
    pattern_type = pattern_info.get("type")
    
    if pattern_type == "definition_query":
        return build_definition_answer(pattern_info, paths, node)
    elif pattern_type == "property_query":
        return build_property_answer(pattern_info, paths)
    else:
        return "I don't know how to answer that."


def build_definition_answer(pattern_info, paths, node=None):
    subject = pattern_info.get("subject")
    
    if node is None:
        node = get_node(subject)
    
    lines = []
    
    if node and node.definition:
        lines.append(f"{subject.capitalize()}: {node.definition}")
    
    related_paths = [p for p in paths if p["relation"] == "related_to" and p["from"] == subject]
    
    if related_paths:
        related_words = [p["to"] for p in related_paths[:5]]
        lines.append(f"\nRelated concepts: {', '.join(related_words)}")
        
        for rel_path in related_paths[:3]:
            rel_word = rel_path["to"]
            rel_node = get_node(rel_word)
            if rel_node and rel_node.definition:
                short_def = rel_node.definition[:60] + "..." if len(rel_node.definition) > 60 else rel_node.definition
                lines.append(f"  • {rel_word}: {short_def}")
    
    if lines:
        return "\n".join(lines)
    
    is_a_paths = [p for p in paths if p["relation"] == "is_a"]
    
    if is_a_paths:
        best = is_a_paths[0]
        confidence = best["confidence"]
        
        if confidence == 1.0:
            return f"{subject.capitalize()} is a {best['to']}."
        else:
            pct = int(confidence * 100)
            return f"{subject.capitalize()} is most likely a {best['to']} ({pct}% confidence)."
    
    return ask_clarifying_question(subject)


def build_property_answer(pattern_info, paths):
    subject = pattern_info.get("subject")
    property_name = pattern_info.get("property")
    
    if not paths:
        return None
    
    yes_paths = [p for p in paths if p["to"] == "yes"]
    no_paths = [p for p in paths if p["to"] == "no"]
    
    best_yes = max(yes_paths, key=lambda x: x["confidence"]) if yes_paths else None
    best_no = max(no_paths, key=lambda x: x["confidence"]) if no_paths else None
    
    if best_yes and best_no:
        if best_yes["confidence"] > best_no["confidence"]:
            pct = int(best_yes["confidence"] * 100)
            return f"Most likely yes, {subject} is {property_name} ({pct}% confidence)."
        else:
            pct = int(best_no["confidence"] * 100)
            return f"Most likely no, {subject} is not {property_name} ({pct}% confidence)."
    elif best_yes:
        if best_yes["confidence"] == 1.0:
            return f"Yes, {subject} is {property_name}."
        else:
            pct = int(best_yes["confidence"] * 100)
            return f"Most likely yes ({pct}% confidence)."
    elif best_no:
        if best_no["confidence"] == 1.0:
            return f"No, {subject} is not {property_name}."
        else:
            pct = int(best_no["confidence"] * 100)
            return f"Most likely no ({pct}% confidence)."
    
    return None


def format_paths(paths):
    if not paths:
        return "No paths found."
    
    lines = ["PATHS FOUND:"]
    for p in paths:
        conf = f" ({int(p['confidence']*100)}%)" if p['confidence'] < 1.0 else ""
        lines.append(f"  {p['from']} → {p['relation']} → {p['to']}{conf}")
    
    return "\n".join(lines)
