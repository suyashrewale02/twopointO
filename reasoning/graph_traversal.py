from db.crud import get_node, get_paths_from, get_node_by_id

MAX_DEPTH = 10
PREFERRED_RELATIONS = ["is_a", "definition", "means", "is", "related_to"]


def traverse(start_word, max_depth=MAX_DEPTH, relation_filter=None):
    paths_found = []
    visited = set()
    
    def _traverse(word, depth, current_path):
        if depth > max_depth:
            return
        if word in visited:
            return
        
        visited.add(word)
        node = get_node(word)
        if not node:
            return
        
        paths = get_paths_from(word, relation_type=relation_filter)
        
        for path in paths:
            to_node = get_node_by_id(path.to_connection)
            if to_node:
                path_entry = {
                    "from": word,
                    "relation": path.relation_type,
                    "to": to_node.connection_text,
                    "confidence": path.confidence,
                    "depth": depth
                }
                paths_found.append(path_entry)
                
                _traverse(to_node.connection_text, depth + 1, current_path + [path_entry])
    
    _traverse(start_word, 0, [])
    
    paths_found.sort(key=lambda x: (-x["confidence"], PREFERRED_RELATIONS.index(x["relation"]) if x["relation"] in PREFERRED_RELATIONS else 100))
    
    return paths_found


def traverse_deep(start_word, max_depth=MAX_DEPTH):
    tree = {"word": start_word, "children": [], "depth": 0}
    visited = set()
    all_paths = []
    
    def _build_tree(node_dict, depth):
        if depth >= max_depth:
            return
        
        word = node_dict["word"]
        if word in visited:
            return
        
        visited.add(word)
        db_node = get_node(word)
        if not db_node:
            return
        
        node_dict["type"] = db_node.type
        node_dict["definition"] = db_node.definition
        
        paths = get_paths_from(word)
        
        for path in paths:
            to_node = get_node_by_id(path.to_connection)
            if to_node and to_node.connection_text not in visited:
                child = {
                    "word": to_node.connection_text,
                    "relation": path.relation_type,
                    "confidence": path.confidence,
                    "children": [],
                    "depth": depth + 1
                }
                node_dict["children"].append(child)
                
                all_paths.append({
                    "from": word,
                    "relation": path.relation_type,
                    "to": to_node.connection_text,
                    "confidence": path.confidence,
                    "depth": depth
                })
                
                _build_tree(child, depth + 1)
    
    _build_tree(tree, 0)
    
    return tree, all_paths


def format_tree(tree, indent=0):
    lines = []
    prefix = "  " * indent
    
    word = tree.get("word", "?")
    relation = tree.get("relation", "")
    confidence = tree.get("confidence", 1.0)
    node_type = tree.get("type", "")
    
    if relation:
        conf_str = f" ({int(confidence*100)}%)" if confidence < 1.0 else ""
        lines.append(f"{prefix}└─ {relation} → {word} [{node_type}]{conf_str}")
    else:
        lines.append(f"{prefix}{word} [{node_type}]")
    
    for child in tree.get("children", []):
        lines.extend(format_tree(child, indent + 1))
    
    return lines


def find_paths(from_word, to_word=None, relation_type=None, max_depth=MAX_DEPTH):
    all_paths = traverse(from_word, max_depth=max_depth, relation_filter=relation_type)
    
    if to_word:
        all_paths = [p for p in all_paths if p["to"] == to_word.lower()]
    
    return all_paths


def find_definition(word):
    paths = find_paths(word, relation_type="is_a")
    if paths:
        return paths[0]
    
    paths = find_paths(word, relation_type="definition")
    if paths:
        return paths[0]
    
    return None


def find_property(subject, property_name):
    relation = f"is_{property_name.replace(' ', '_')}"
    paths = find_paths(subject, relation_type=relation)
    
    if paths:
        best = max(paths, key=lambda x: x["confidence"])
        return best
    
    return None
