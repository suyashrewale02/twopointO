from db.connection import get_session, Node, Connection

def get_node_id(label):
    """Get node ID by label."""
    session = get_session()
    node = session.query(Node).filter(Node.label == label).first()
    session.close()
    return node.id if node else None

def get_node_label(node_id):
    """Get node label by ID."""
    session = get_session()
    node = session.query(Node).filter(Node.id == node_id).first()
    session.close()
    return node.label if node else None

def get_connections(node_id):
    """Get all connections where node_id is in from_node_id or to_node_id."""
    session = get_session()
    connections = session.query(Connection).filter(
        (Connection.from_node_id == node_id) | (Connection.to_node_id == node_id)
    ).all()
    results = []
    for c in connections:
        results.append({
            "id": c.id,
            "from_node_id": c.from_node_id,
            "to_node_id": c.to_node_id,
            "relation_strength": c.relation_strength,
            "use_count": c.use_count
        })
    session.close()
    return results

def traverse_node(label):
    """Find and print connections for a node."""
    print("\n--- Printing from traversal ---")
    node_id = get_node_id(label)
    if node_id:
        connections = get_connections(node_id)
        if connections:
            print(f"  Connections for {label}:")
            for conn in connections:
                print(f"    id={conn['id']}, from={conn['from_node_id']}, to={conn['to_node_id']}, strength={conn['relation_strength']}, use_count={conn['use_count']}")
                
                # Find connected node label
                if conn['from_node_id'] == node_id:
                    connected_label = get_node_label(conn['to_node_id'])
                else:
                    connected_label = get_node_label(conn['from_node_id'])
                print(f"      -> connected node: {connected_label}")
        return connections
    return []
