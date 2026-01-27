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
        # Increment use_count
        c.use_count = (c.use_count or 0) + 1
        results.append({
            "id": c.id,
            "from_node_id": c.from_node_id,
            "to_node_id": c.to_node_id,
            "relation_strength": c.relation_strength,
            "use_count": c.use_count
        })
    session.commit()
    session.close()
    return results

def traverse_node(label, max_generations=5):
    """Find and print connections for a node up to max_generations deep."""
    print("\n--- Printing from traversal ---")
    print(f"  Parent: {label}")
    
    node_id = get_node_id(label)
    if not node_id:
        print(f"  Node '{label}' not found")
        return []
    
    visited = set()
    visited.add(node_id)
    current_gen_ids = [node_id]
    all_connections = []
    
    parent_id = node_id
    
    for gen in range(1, max_generations + 1):
        if not current_gen_ids:
            break
            
        print(f"\n  Generation {gen}:")
        next_gen_ids = []
        
        for current_id in current_gen_ids:
            connections = get_connections(current_id)
            
            for conn in connections:
                # Find connected node id
                if conn['from_node_id'] == current_id:
                    connected_id = conn['to_node_id']
                else:
                    connected_id = conn['from_node_id']
                
                # Skip if connected node is the parent
                if connected_id == parent_id and gen > 1:
                    continue
                
                all_connections.append(conn)
                connected_label = get_node_label(connected_id)
                print(f"    {connected_label} [{conn['from_node_id']} to {conn['to_node_id']}, strength={conn['relation_strength']}, use_count={conn['use_count']}]")
                
                # Add to next generation if not visited
                if connected_id not in visited:
                    visited.add(connected_id)
                    next_gen_ids.append(connected_id)
        
        current_gen_ids = next_gen_ids
    
    return all_connections
