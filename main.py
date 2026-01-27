import sys
sys.path.insert(0, '.')

from db.models import init_db
from db.crud import get_node, create_path, get_or_create_node, adjust_competing_paths
from learning.word_learner import learn_word, learn_word_from_user, learn_word_deep
from learning.grammar_learner import detect_pattern, init_grammar_patterns
from learning.meaning_learner import learn_relation, learn_property
from reasoning.parser import tokenize
from reasoning.graph_traversal import traverse, find_property, traverse_deep, format_tree
from reasoning.answer_builder import build_answer, build_property_answer, format_paths


def ask_user_for_word(word):
    print(f"\n  I don't know the word '{word}'. Please teach me:")
    print(f"  What is the definition of '{word}'?")
    definition = input("  Definition: ").strip()
    if not definition:
        return None
    
    print(f"  What type of word is '{word}'? (noun, verb, adjective, etc.)")
    word_type = input("  Type: ").strip().lower()
    if not word_type:
        word_type = "unknown"
    
    node = learn_word_from_user(word, definition, word_type)
    print(f"  Learned '{word}' from user.")
    return node


def process_query(query):
    print(f"\n{'='*50}")
    print(f"STEP 1 — Receive Query: \"{query}\"")
    
    print(f"\nSTEP 2 — Tokenize:")
    tokens = tokenize(query)
    print(f"  Tokens: {tokens}")
    
    print(f"\nSTEP 3 — Word-Level Node Check:")
    print(f"  {'Word':<15} {'Exists?':<10} {'Action':<15} {'Source'}")
    print(f"  {'-'*55}")
    
    for token in tokens:
        existing = get_node(token)
        if existing:
            print(f"  {token:<15} {'✓':<10} {'skip':<15} database")
        else:
            node, created, source, connections = learn_word_deep(token, max_depth=2)
            if created:
                print(f"  {token:<15} {'✗':<10} {'learned':<15} {source}")
                if node and node.definition:
                    print(f"    → {node.type}: {node.definition[:60]}{'...' if len(node.definition or '') > 60 else ''}")
                if len(connections) > 0:
                    print(f"    → Deep connections: {len(connections)}")
            elif node:
                print(f"  {token:<15} {'✓':<10} {'exists':<15} {source}")
            else:
                print(f"  {token:<15} {'✗':<10} {'NOT FOUND':<15} -")
                node = ask_user_for_word(token)
                if node:
                    print(f"    → {node.type}: {node.definition[:60]}{'...' if len(node.definition or '') > 60 else ''}")
    
    print(f"\nSTEP 4 — Grammar Recognition:")
    pattern_info = detect_pattern(tokens)
    if pattern_info:
        print(f"  Pattern: {pattern_info['pattern']}")
        print(f"  Type: {pattern_info['type']}")
        print(f"  Expects: {pattern_info.get('expects', 'N/A')}")
    else:
        print(f"  No pattern recognized.")
        return tokens, None
    
    return tokens, pattern_info


def handle_definition_query(pattern_info):
    subject = pattern_info["subject"]
    subject_words = subject.split()
    
    from db.crud import get_paths_from
    existing_node = get_node(subject)
    existing_paths = get_paths_from(subject) if existing_node else []
    
    if existing_node and existing_node.definition and len(existing_paths) >= 3:
        print(f"\nSTEP 5 — Quick Lookup ('{subject}' already known):")
        print(f"  Found in DB with {len(existing_paths)} connections")
        
        print(f"\nSTEP 6 — Answer:")
        paths = traverse(subject, max_depth=3)
        related = [p["to"] for p in paths if p["relation"] == "related_to"][:5]
        
        print(f"  {subject.capitalize()}: {existing_node.definition}")
        if related:
            print(f"\n  Related concepts: {', '.join(related)}")
        
        return paths, None, None
    
    if len(subject_words) > 1 and not existing_node:
        print(f"\nSTEP 5 — Combined subject '{subject}' not found. Trying individual words:")
        all_word_paths = []
        word_definitions = {}
        
        for word in subject_words:
            word_node = get_node(word)
            if word_node and word_node.definition:
                print(f"  Found '{word}': {word_node.definition[:60]}...")
                word_definitions[word] = word_node.definition
                word_paths = traverse(word, max_depth=3)
                all_word_paths.extend(word_paths)
        
        if word_definitions:
            print(f"\nSTEP 6 — Answer (from individual words):")
            for word, defn in word_definitions.items():
                print(f"  • {word}: {defn}")
            return all_word_paths, None, None
    
    print(f"\nSTEP 5 — Deep Learning (expanding '{subject}' up to 10 levels):")
    print(f"  Learning tree:")
    node, created, source, connections = learn_word_deep(subject, current_depth=0, max_depth=10)
    
    print(f"\n  Total connections made: {len(connections)}")
    if connections:
        by_depth = {}
        for c in connections:
            d = c['depth']
            if d not in by_depth:
                by_depth[d] = []
            by_depth[d].append(c)
        for depth in sorted(by_depth.keys()):
            print(f"    Depth {depth}: {len(by_depth[depth])} connections")
    
    print(f"\nSTEP 6 — Graph Traversal (from '{subject}', max depth 10):")
    tree, all_paths = traverse_deep(subject, max_depth=10)
    
    tree_lines = format_tree(tree)
    for line in tree_lines:
        print(f"  {line}")
    
    print(f"\nSTEP 7 — All Paths Found ({len(all_paths)} paths):")
    if all_paths:
        for p in all_paths[:20]:
            conf = f" ({int(p['confidence']*100)}%)" if p['confidence'] < 1.0 else ""
            indent = "  " * p.get('depth', 0)
            print(f"  {indent}{p['from']} → {p['relation']} → {p['to']}{conf}")
        if len(all_paths) > 20:
            print(f"  ... and {len(all_paths) - 20} more paths")
    else:
        print("  No paths found.")
    
    print(f"\nSTEP 8 — Answer:")
    answer = build_answer(pattern_info, all_paths)
    print(f"  {answer}")
    
    if "?" in answer or "Can you" in answer or "What" in answer:
        return all_paths, "clarification", {"subject": subject, "original_query": pattern_info}
    
    return all_paths, None, None


def handle_property_of_query(pattern_info):
    """Handle 'what is X of Y?' queries - asking for property X of entity Y"""
    property_name = pattern_info["property"]
    entity = pattern_info["entity"]
    
    print(f"\nSTEP 5 — Looking for '{property_name}' of '{entity}':")
    
    entity_node = get_node(entity)
    paths = traverse(entity, max_depth=5)
    property_paths = [p for p in paths if property_name in p.get("relation", "") or property_name in p.get("to", "")]
    
    if property_paths:
        print(f"  Found {len(property_paths)} relevant paths")
        print(f"\nSTEP 6 — Answer:")
        for p in property_paths[:5]:
            print(f"  {entity} → {p['relation']} → {p['to']}")
        return paths, True
    
    print(f"  No direct '{property_name}' found. Trying deep learning...")
    
    print(f"\nSTEP 5.1 — Deep Learning '{entity}' to find '{property_name}':")
    node, created, source, connections = learn_word_deep(entity, max_depth=3)
    
    paths = traverse(entity, max_depth=5)
    property_paths = [p for p in paths if property_name in p.get("relation", "") or property_name in p.get("to", "")]
    
    if property_paths:
        print(f"  Found {len(property_paths)} paths after deep learning!")
        print(f"\nSTEP 6 — Answer:")
        for p in property_paths[:5]:
            print(f"  {entity} → {p['relation']} → {p['to']}")
        return paths, True
    
    print(f"\nSTEP 5.2 — Checking related concepts for '{property_name}':")
    related_paths = traverse(entity, max_depth=3)
    for p in related_paths:
        related_word = p.get("to", "")
        if related_word:
            related_node = get_node(related_word)
            if related_node and related_node.definition:
                if property_name in related_node.definition.lower():
                    print(f"  Found '{property_name}' hint in related concept '{related_word}'")
                    print(f"    Definition: {related_node.definition[:80]}...")
                    
                    related_deeper = traverse(related_word, max_depth=2)
                    for rp in related_deeper:
                        if property_name in rp.get("relation", "").lower() or property_name in rp.get("to", "").lower():
                            print(f"\nSTEP 6 — Answer (via '{related_word}'):")
                            print(f"  {entity} → related_to → {related_word} → {rp['relation']} → {rp['to']}")
                            create_path(entity, f"has_{property_name}", rp['to'], confidence=0.7)
                            return paths, True
    
    print(f"\nSTEP 5.3 — Deep Learning '{property_name}' for reverse lookup:")
    prop_node, prop_created, prop_source, prop_conns = learn_word_deep(property_name, max_depth=2)
    
    if prop_node and prop_node.definition:
        entity_node = get_node(entity)
        if entity_node and entity_node.definition:
            from learning.word_learner import extract_definition_words
            prop_words = set(extract_definition_words(prop_node.definition))
            entity_words = set(extract_definition_words(entity_node.definition))
            shared = prop_words & entity_words
            if shared:
                print(f"  Shared concepts: {', '.join(list(shared)[:5])}")
    
    print(f"\n  Could not find '{property_name}' of '{entity}' through deep learning.")
    print(f"\nSTEP 6 — Learning from user:")
    print(f"  What is the {property_name} of {entity}?")
    answer = input("  > ").strip()
    
    if answer and answer.lower() != 'skip':
        get_or_create_node(answer, node_type=property_name)
        create_path(entity, f"has_{property_name}", answer, confidence=1.0)
        print(f"  Learned: {entity} has {property_name} → {answer}")
        return [], True
    return [], False


def handle_property_query(pattern_info):
    subject = pattern_info["subject"]
    property_name = pattern_info["property"]
    relation = f"is_{property_name.replace(' ', '_')}"
    
    print(f"\nSTEP 5 — Graph Traversal (from '{subject}', relation '{relation}'):")
    paths = traverse(subject, max_depth=10, relation_filter=relation)
    
    if paths:
        print(format_paths(paths))
        print(f"\nSTEP 6 — Answer:")
        answer = build_property_answer(pattern_info, paths)
        print(f"  {answer}")
        return paths, True
    else:
        print("  No paths found.")
        return [], False


def ask_user_for_property(subject, property_name):
    print(f"\n  I do not know if {subject} is {property_name}.")
    print(f"  Answer yes or no:")
    answer = input("  > ").strip().lower()
    
    if answer in ["yes", "no"]:
        relation = f"is_{property_name.replace(' ', '_')}"
        get_or_create_node(answer, node_type="boolean")
        create_path(subject, relation, answer, confidence=1.0)
        if answer == "yes":
            print(f"  Learned: Yes, {subject} is {property_name}.")
        else:
            print(f"  Learned: No, {subject} is not {property_name}.")
        return True
    else:
        print("  Please answer yes or no.")
        return False


def handle_correction(subject, property_name, new_answer):
    if new_answer not in ["yes", "no"]:
        return False
    
    relation = f"is_{property_name.replace(' ', '_')}"
    get_or_create_node(new_answer, node_type="boolean")
    create_path(subject, relation, new_answer, confidence=0.5)
    adjust_competing_paths(subject, relation, new_answer)
    
    print(f"  Updated knowledge about {subject} being {property_name}.")
    return True


def handle_inferred_query(pattern_info):
    """Handle queries where intent was inferred from graph traversal"""
    intent = pattern_info.get("intent", "unknown")
    focus = pattern_info.get("focus", "")
    definitions = pattern_info.get("definitions", {})
    related = pattern_info.get("related", {})
    options = pattern_info.get("clarifying_options", [])
    pattern_match = pattern_info.get("pattern_match", {})
    tokens = pattern_info.get("tokens", [])
    
    print(f"\nSTEP 5 — Intent Inference (analyzing against known patterns):")
    print(f"  Inferred intent: {intent}")
    print(f"  Focus word: '{focus}'")
    
    if intent == "greeting" and focus:
        print(f"\n  This looks like a greeting!")
        print(f"  How should I respond to '{focus}'?")
        response = input("  Response: ").strip()
        if response:
            pattern_key = " ".join(tokens) if tokens else focus
            get_or_create_node(pattern_key, node_type="learned_pattern")
            get_or_create_node(response, node_type="response")
            create_path(pattern_key, "responds_with", response, confidence=1.0)
            create_path(pattern_key, "pattern_type", "greeting", confidence=1.0)
            print(f"  Learned: '{pattern_key}' → responds_with → '{response}'")
        return
    
    if intent == "request" and focus:
        print(f"\n  This looks like an indirect request about '{focus}'!")
        print(f"  I know these patterns for requests:")
        print(f"    1. \"what is {focus}?\" - ask for definition")
        print(f"    2. \"tell me {focus}\" - request information")
        print(f"    3. Teach me how to respond to this specific phrase")
        choice = input("  Choose (1/2/3): ").strip()
        
        if choice == "1":
            print(f"\n  Converting to: 'what is {focus}?'")
            from reasoning.parser import tokenize
            new_tokens = tokenize(f"what is {focus}?")
            from learning.grammar_learner import detect_pattern
            new_pattern = detect_pattern(new_tokens)
            if new_pattern:
                print(f"  Pattern recognized: {new_pattern['type']}")
        elif choice == "2":
            print(f"\n  Converting to: 'tell me {focus}'")
        elif choice == "3":
            print(f"  What should I respond to '{' '.join(tokens)}'?")
            response = input("  Response: ").strip()
            if response:
                pattern_key = " ".join(tokens)
                get_or_create_node(pattern_key, node_type="learned_pattern")
                get_or_create_node(response, node_type="response")
                create_path(pattern_key, "responds_with", response, confidence=1.0)
                create_path(pattern_key, "pattern_type", "request", confidence=1.0)
                print(f"  Learned: '{pattern_key}' → responds_with → '{response}'")
        return
    
    if pattern_match:
        closest = pattern_match.get("closest_pattern", {})
        suggestions = pattern_match.get("suggestions", [])
        all_matches = pattern_match.get("all_matches", [])
        
        print(f"\n  Closest known pattern: '{closest.get('name', 'unknown')}'")
        print(f"  Pattern type: {closest.get('type', 'unknown')}")
        print(f"  Example: {closest.get('example', '')}")
        
        if all_matches and len(all_matches) > 1:
            print(f"\n  Other possible patterns:")
            for pat, score in all_matches[1:3]:
                print(f"    - '{pat['name']}' (example: {pat['example']})")
    
    if definitions:
        print(f"\n  Definitions found:")
        for word, defn in definitions.items():
            short_def = defn[:80] + "..." if len(defn) > 80 else defn
            print(f"    {word}: {short_def}")
    
    print(f"\nSTEP 6 — Pattern-Based Clarification:")
    
    if pattern_match and pattern_match.get("suggestions"):
        suggestions = pattern_match["suggestions"]
        print(f"  I think you might be trying to say one of these:")
        for i, s in enumerate(suggestions[:3], 1):
            print(f"    {i}. \"{s}\"")
        print(f"  Which one matches your intent? (1/2/3 or rephrase)")
        
        answer = input("  > ").strip()
        
        if answer in ["1", "2", "3"]:
            idx = int(answer) - 1
            if idx < len(suggestions):
                suggested = suggestions[idx]
                print(f"\n  Processing: '{suggested}'")
                from reasoning.parser import tokenize
                new_tokens = tokenize(suggested)
                from learning.grammar_learner import detect_pattern
                new_pattern = detect_pattern(new_tokens)
                if new_pattern and new_pattern["type"] != "inferred_query":
                    print(f"  Pattern recognized: {new_pattern['type']}")
        elif answer:
            print(f"  Let me try to understand '{answer}'...")
    elif pattern_match:
        closest = pattern_match.get("closest_pattern", {})
        print(f"  Your input seems similar to '{closest.get('name', 'unknown')}'")
        print(f"  Try rephrasing like: \"{closest.get('example', '')}\"")
        answer = input("  > ").strip()
    else:
        print(f"  I couldn't match this to any known pattern.")
        print(f"  Known patterns I understand:")
        from learning.grammar_learner import get_known_patterns
        for p in get_known_patterns()[:5]:
            print(f"    - {p['name']} (e.g., \"{p['example']}\")")
        print(f"  Try rephrasing using one of these formats.")
        answer = input("  > ").strip()


def handle_opinion_query(pattern_info):
    """Handle 'what do you think about X?' type questions"""
    topic = pattern_info.get("topic", "")
    
    print(f"\nSTEP 5 — Opinion Query (asking about '{topic}'):")
    
    self_node = get_node("self")
    if not self_node:
        get_or_create_node("self", node_type="entity", definition="The Knowledge Graph AI system")
    
    paths = traverse("self", max_depth=3)
    opinion_paths = [p for p in paths if topic in p.get("to", "").lower() or f"opinion_{topic}" in p.get("relation", "")]
    
    if opinion_paths:
        print(f"  Found opinion about '{topic}'")
        print(f"\nSTEP 6 — Answer:")
        print(f"  {opinion_paths[0]['to']}")
        return
    
    topic_node = get_node(topic)
    if topic_node and topic_node.definition:
        print(f"  I know about '{topic}': {topic_node.definition[:60]}...")
    else:
        print(f"  Learning about '{topic}' first...")
        node, created, source, connections = learn_word_deep(topic, max_depth=2)
        if node and node.definition:
            print(f"  Learned: {node.definition[:60]}...")
    
    print(f"\nSTEP 6 — Learning my opinion:")
    print(f"  What do I think about '{topic}'?")
    answer = input("  > ").strip()
    
    if answer and answer.lower() != 'skip':
        get_or_create_node(answer, node_type="opinion")
        create_path("self", f"opinion_{topic}", answer, confidence=1.0)
        print(f"  Learned: My opinion on '{topic}' is '{answer}'")


def handle_self_state_query(pattern_info):
    """Handle 'how are you?' type questions about AI's state"""
    print(f"\nSTEP 5 — Self State Query:")
    
    self_node = get_node("self")
    if not self_node:
        get_or_create_node("self", node_type="entity", definition="The Knowledge Graph AI system")
    
    paths = traverse("self", max_depth=3)
    state_paths = [p for p in paths if "state" in p.get("relation", "") or "feeling" in p.get("relation", "")]
    
    if state_paths:
        print(f"  Found: self → {state_paths[0]['relation']} → {state_paths[0]['to']}")
        print(f"\nSTEP 6 — Answer:")
        print(f"  I'm {state_paths[0]['to']}!")
        return
    
    print(f"  I don't have a state response set yet.")
    print(f"\nSTEP 6 — Learning:")
    print(f"  How should I respond to 'how are you?'")
    answer = input("  > ").strip()
    
    if answer and answer.lower() != 'skip':
        get_or_create_node(answer, node_type="state")
        create_path("self", "has_state", answer, confidence=1.0)
        create_path("how are you ?", "responds_with", answer, confidence=1.0)
        get_or_create_node("how are you ?", node_type="learned_pattern")
        create_path("how are you ?", "pattern_type", "greeting", confidence=1.0)
        print(f"  Learned: I'll respond with '{answer}'")


def handle_self_query(pattern_info):
    """Handle questions about the AI itself like 'what is your name?'"""
    property_name = pattern_info.get("property", "")
    possessive = pattern_info.get("possessive", "your")
    
    print(f"\nSTEP 5 — Self Query (asking about AI's '{property_name}'):")
    
    self_node = get_node("self")
    if not self_node:
        get_or_create_node("self", node_type="entity", definition="The Knowledge Graph AI system")
    
    paths = traverse("self", max_depth=3)
    property_paths = [p for p in paths if property_name in p.get("relation", "") or property_name in p.get("to", "")]
    
    if property_paths:
        print(f"  Found: self → {property_paths[0]['relation']} → {property_paths[0]['to']}")
        print(f"\nSTEP 6 — Answer:")
        print(f"  My {property_name} is {property_paths[0]['to']}")
        return
    
    print(f"  I don't have a '{property_name}' set yet.")
    print(f"\nSTEP 6 — Learning:")
    print(f"  What is my {property_name}?")
    answer = input("  > ").strip()
    
    if answer and answer.lower() != 'skip':
        get_or_create_node(answer, node_type=property_name)
        create_path("self", f"has_{property_name}", answer, confidence=1.0)
        print(f"  Learned: self has {property_name} → {answer}")


def handle_request(pattern_info):
    verb = pattern_info.get("verb", "")
    target = pattern_info.get("target", "")
    obj = pattern_info.get("object", "")
    
    print(f"\nSTEP 5 — Processing Request:")
    print(f"  Verb: {verb}")
    print(f"  Target: {target or 'none'}")
    print(f"  Object: {obj}")
    
    node = get_node(obj)
    if node and node.definition:
        print(f"\nSTEP 6 — Found '{obj}' in knowledge graph:")
        print(f"  {obj.capitalize()}: {node.definition}")
        
        tree, paths = traverse_deep(obj, max_depth=3)
        if paths:
            related = [p["to"] for p in paths if p["relation"] == "related_to"][:5]
            if related:
                print(f"\n  Related concepts: {', '.join(related)}")
    else:
        print(f"\n  I don't know about '{obj}' yet.")
        print(f"  Would you like to teach me? (yes/no)")
        answer = input("  > ").strip().lower()
        if answer == "yes":
            print(f"  What is the definition of '{obj}'?")
            definition = input("  Definition: ").strip()
            if definition:
                print(f"  What type of word is '{obj}'?")
                word_type = input("  Type: ").strip().lower() or "noun"
                from learning.word_learner import learn_word_from_user
                learn_word_from_user(obj, definition, word_type)
                print(f"  Learned '{obj}'!")


def handle_context_answer(answer, question_type, context):
    """Handle user's answer to a clarifying question"""
    answer_lower = answer.lower().strip()
    
    if question_type == "yes_no":
        if answer_lower in ["yes", "y"]:
            return context.get("yes_response", "Great! Let me continue...")
        elif answer_lower in ["no", "n"]:
            return context.get("no_response", "I see. Can you tell me more?")
    
    return None


def handle_special_query(pattern_info):
    query_type = pattern_info.get("type", "")
    subject = pattern_info.get("subject", "")
    expects = pattern_info.get("expects", "")
    question_word = pattern_info.get("question_word", "")
    
    print(f"\nSTEP 5 — Processing {query_type}:")
    print(f"  Looking for: {expects} of '{subject}'")
    
    node = get_node(subject)
    if node:
        print(f"\nSTEP 6 — Found '{subject}':")
        print(f"  Type: {node.type or 'unknown'}")
        if node.definition:
            print(f"  Definition: {node.definition}")
        
        paths = traverse(subject, max_depth=5)
        relevant_paths = [p for p in paths if expects in p.get("relation", "") or expects in p.get("to", "")]
        
        if relevant_paths:
            print(f"\n  Related {expects} information:")
            for p in relevant_paths[:5]:
                print(f"    {p['from']} → {p['relation']} → {p['to']}")
        else:
            print(f"\n  No specific {expects} information found for '{subject}'.")
    else:
        print(f"\n  I don't know '{subject}' yet.")


def main():
    print("Initializing database...")
    init_db()
    init_grammar_patterns()
    print("Knowledge Graph Ready.")
    print("Supports: 'what is X?' and 'is X Y?'")
    print("Type 'exit' to quit.\n")
    
    pending_subject = None
    pending_property = None
    pending_question = None
    pending_context = None
    
    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break
        
        if user_input.lower() == "exit":
            print("Goodbye!")
            break
        
        if not user_input:
            continue
        
        if pending_question and pending_context:
            response = handle_context_answer(user_input, pending_question, pending_context)
            if response:
                print(f"\n{response}")
                pending_question = None
                pending_context = None
                continue
        
        if user_input.lower() in ["yes", "no"] and pending_subject and pending_property:
            handle_correction(pending_subject, pending_property, user_input.lower())
            pending_subject = None
            pending_property = None
            continue
        
        tokens, pattern_info = process_query(user_input)
        
        if not pattern_info:
            if pending_question == "clarification" and pending_context:
                new_subject = user_input.strip()
                print(f"\n  Interpreting '{new_subject}' as subject for definition query...")
                new_pattern = {
                    "pattern": "what_is_x",
                    "type": "definition_query",
                    "subject": new_subject,
                    "expects": "definition"
                }
                result = handle_definition_query(new_pattern)
                if isinstance(result, tuple) and len(result) == 3:
                    paths, question_type, context = result
                    if question_type:
                        pending_question = question_type
                        pending_context = context
                    else:
                        pending_question = None
                        pending_context = None
                else:
                    pending_question = None
                    pending_context = None
                continue
            
            print("\n  I don't recognize this pattern. Can you teach me?")
            print("  What does this mean? (or type 'skip' to skip)")
            explanation = input("  > ").strip()
            
            if explanation.lower() != 'skip' and explanation:
                pattern_key = " ".join([t.lower() for t in tokens])
                
                print(f"  What type of response should this give? (greeting, question, request, statement)")
                response_type = input("  Type: ").strip().lower() or "statement"
                
                print(f"  What is the answer/response to '{user_input}'?")
                response = input("  Response: ").strip()
                
                if response:
                    pattern_node = get_or_create_node(pattern_key, node_type="learned_pattern", definition=explanation)[0]
                    response_node = get_or_create_node(response, node_type="response", definition=response)[0]
                    
                    create_path(pattern_key, "responds_with", response, confidence=1.0)
                    create_path(pattern_key, "pattern_type", response_type, confidence=1.0)
                    
                    print(f"\n  Deep learning on response...")
                    for word in tokens:
                        if word not in ['?', '.', '!', ',']:
                            create_path(pattern_key, "contains_word", word.lower(), confidence=1.0)
                            create_path(word.lower(), "used_in_pattern", response_type, confidence=0.8)
                    
                    from reasoning.parser import tokenize as tok
                    response_tokens = tok(response)
                    for rt in response_tokens[:5]:
                        if rt not in ['?', '.', '!', ','] and len(rt) > 2:
                            node, created, src, conns = learn_word_deep(rt, max_depth=2)
                            if node:
                                create_path(response, "contains_concept", rt.lower(), confidence=0.9)
                    
                    print(f"  Learned pattern: '{pattern_key}' → responds_with → '{response}'")
                    print(f"  Connected words: {[t for t in tokens if t not in ['?', '.', '!', ',']]}")
            continue
        
        if pattern_info["type"] == "self_query":
            handle_self_query(pattern_info)
            pending_subject = None
            pending_property = None
        
        elif pattern_info["type"] == "self_state_query":
            handle_self_state_query(pattern_info)
            pending_subject = None
            pending_property = None
        
        elif pattern_info["type"] == "opinion_query":
            handle_opinion_query(pattern_info)
            pending_subject = None
            pending_property = None
        
        elif pattern_info["type"] == "definition_query":
            result = handle_definition_query(pattern_info)
            if isinstance(result, tuple) and len(result) == 3:
                paths, question_type, context = result
                if question_type:
                    pending_question = question_type
                    pending_context = context
            pending_subject = None
            pending_property = None
        
        elif pattern_info["type"] == "property_of_query":
            handle_property_of_query(pattern_info)
            pending_subject = None
            pending_property = None
            
        elif pattern_info["type"] == "property_query":
            subject = pattern_info["subject"]
            property_name = pattern_info["property"]
            
            paths, found = handle_property_query(pattern_info)
            
            if not found:
                ask_user_for_property(subject, property_name)
            
            pending_subject = subject
            pending_property = property_name
        
        elif pattern_info["type"] == "request":
            handle_request(pattern_info)
            pending_subject = None
            pending_property = None
        
        elif pattern_info["type"] == "inferred_query":
            handle_inferred_query(pattern_info)
            pending_subject = None
            pending_property = None
        
        elif pattern_info["type"].endswith("_query"):
            handle_special_query(pattern_info)
            pending_subject = None
            pending_property = None
        
        elif pattern_info["type"] == "learned_response":
            print(f"\nSTEP 5 — Learned Pattern Recognized:")
            print(f"  Pattern: {pattern_info.get('pattern_key', '')}")
            print(f"  Type: {pattern_info.get('response_type', 'learned')}")
            if pattern_info.get("similarity_score"):
                print(f"  Similarity: {pattern_info['similarity_score']:.0%}")
                if pattern_info.get('shared_words'):
                    print(f"  Direct matches: {', '.join(pattern_info.get('shared_words', []))}")
                if pattern_info.get('deep_matches'):
                    print(f"  Deep matches: {', '.join(pattern_info.get('deep_matches', []))}")
                if pattern_info.get('depth_searched'):
                    print(f"  Depth searched: {pattern_info['depth_searched']}")
            print(f"\nResponse: {pattern_info.get('response', '')}")
            pending_subject = None
            pending_property = None


if __name__ == "__main__":
    main()
