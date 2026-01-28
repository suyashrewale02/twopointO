import math
from db.connection import get_session, Node, Connection

# Decay factors per generation
DECAY_FACTORS = {1: 1.0, 2: 0.8, 3: 0.6, 4: 0.4, 5: 0.2}

def calculate_strength(use_count, node_type, generation):
    """Calculate strength based on use_count, node_type, and generation."""
    base_strength = 0.01
    increment = math.log(1 + use_count) / 100
    base_strength_new = base_strength + increment
    
    # Modifier based on node_type
    modifier = 1.0
    if node_type in ["perceptual", "action"]:
        modifier = 1.1  # 10% boost
    
    # Decay factor based on generation
    decay_factor = DECAY_FACTORS.get(generation, 0.2)
    
    return base_strength_new * modifier * decay_factor

def get_node_id(label):
    """Get node ID by label."""
    session = get_session()
    node = session.query(Node).filter(Node.label == label).first()
    session.close()
    return node.id if node else None

def get_node_info(node_id):
    """Get node label and node_type by ID."""
    session = get_session()
    node = session.query(Node).filter(Node.id == node_id).first()
    session.close()
    if node:
        return {"label": node.label, "node_type": node.node_type}
    return None

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
                
                # Skip if connected node is already visited (in higher generation)
                if connected_id in visited and connected_id != parent_id:
                    continue
                
                # Skip if connected node is the parent (after gen 1)
                if connected_id == parent_id and gen > 1:
                    continue
                
                all_connections.append(conn)
                node_info = get_node_info(connected_id)
                
                # Calculate new strength
                strength = calculate_strength(conn['use_count'], node_info['node_type'], gen)
                print(f"    {node_info['label']}: {node_info['node_type']} [{conn['from_node_id']} to {conn['to_node_id']}, strength={strength:.4f}, use_count={conn['use_count']}]")
                
                # Add to next generation if not visited
                if connected_id not in visited:
                    visited.add(connected_id)
                    next_gen_ids.append(connected_id)
        
        current_gen_ids = next_gen_ids
    
    return all_connections
