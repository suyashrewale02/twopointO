import sys
sys.path.insert(0, '.')

from db.models import init_db
from db.crud import get_node, create_path, get_or_create_node, adjust_competing_paths
from learning.word_learner import learn_word, learn_word_from_user, learn_word_deep
from learning.grammar_learner import detect_pattern
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
            node, created, source = learn_word(token)
            if created:
                print(f"  {token:<15} {'✗':<10} {'learned':<15} {source}")
                if node and node.definition:
                    print(f"    → {node.type}: {node.definition[:60]}{'...' if len(node.definition or '') > 60 else ''}")
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
        
        if pattern_info["type"] == "definition_query":
            result = handle_definition_query(pattern_info)
            if isinstance(result, tuple) and len(result) == 3:
                paths, question_type, context = result
                if question_type:
                    pending_question = question_type
                    pending_context = context
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
        
        elif pattern_info["type"].endswith("_query"):
            handle_special_query(pattern_info)
            pending_subject = None
            pending_property = None
        
        elif pattern_info["type"] == "learned_response":
            print(f"\nSTEP 5 — Learned Pattern Recognized:")
            print(f"  Pattern: {pattern_info.get('pattern_key', '')}")
            print(f"  Type: {pattern_info.get('response_type', 'learned')}")
            print(f"\nResponse: {pattern_info.get('response', '')}")
            pending_subject = None
            pending_property = None


if __name__ == "__main__":
    main()
