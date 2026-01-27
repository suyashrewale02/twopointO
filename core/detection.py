from db.connection import get_session, Node

def lookup_token(token):
    """Look up token in node_table and return node data dict or None."""
    session = get_session()
    node = session.query(Node).filter(Node.label == token).first()
    if node:
        # Increment use_count
        node.use_count = (node.use_count or 0) + 1
        session.commit()
        # Extract data before closing session
        result = {
            "label": node.label,
            "node_type": node.node_type,
            "use_count": node.use_count
        }
        session.close()
        return result
    session.close()
    return None

def detect_tokens(tokens):
    """Look up all tokens and return list of results."""
    print("\n--- Printing from detection ---")
    results = []
    for token in tokens:
        node_data = lookup_token(token)
        if node_data:
            results.append(node_data)
        else:
            results.append({
                "label": token,
                "node_type": None,
                "use_count": None
            })
    return results

def classify_query(results):
    """Classify query as 'instruction' or 'understand'."""
    node_types = {r["node_type"] for r in results if r["node_type"]}
    
    if "control" in node_types and "operator" in node_types:
        return "instruction"
    return "Noted!! 👍👍📝"
