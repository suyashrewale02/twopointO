from db.connection import get_session, Node, Connection

def seed():
    session = get_session()
    
    # New nodes
    nodes = [
        {"id": 9, "label": "what", "node_type": "control"},
        {"id": 10, "label": "how", "node_type": "control"},
        {"id": 11, "label": "why", "node_type": "control"},
        {"id": 12, "label": "when", "node_type": "control"},
        {"id": 13, "label": "where", "node_type": "control"},
        {"id": 14, "label": "was", "node_type": "operator"},
        {"id": 15, "label": "were", "node_type": "operator"},
        {"id": 16, "label": "are", "node_type": "operator"},
        {"id": 17, "label": "be", "node_type": "operator"},
        {"id": 18, "label": "i", "node_type": "subject"},
        {"id": 19, "label": "you", "node_type": "subject"},
        {"id": 20, "label": "he", "node_type": "subject"},
        {"id": 21, "label": "she", "node_type": "subject"},
        {"id": 22, "label": "it", "node_type": "subject"},
        {"id": 23, "label": "we", "node_type": "subject"},
        {"id": 24, "label": "they", "node_type": "subject"},
        {"id": 25, "label": "present", "node_type": "tense"},
        {"id": 26, "label": "past", "node_type": "tense"},
        {"id": 27, "label": "future", "node_type": "tense"},
    ]
    
    for n in nodes:
        node = Node(id=n["id"], label=n["label"], node_type=n["node_type"])
        session.merge(node)
    print(f"Added {len(nodes)} nodes")
    
    # New connections
    connections = [
        {"id": 202, "from_node_id": 9, "to_node_id": 8},
        {"id": 203, "from_node_id": 9, "to_node_id": 14},
        {"id": 204, "from_node_id": 9, "to_node_id": 15},
        {"id": 205, "from_node_id": 10, "to_node_id": 8},
        {"id": 206, "from_node_id": 11, "to_node_id": 8},
        {"id": 207, "from_node_id": 12, "to_node_id": 8},
        {"id": 208, "from_node_id": 13, "to_node_id": 8},
        {"id": 209, "from_node_id": 8, "to_node_id": 25},
        {"id": 210, "from_node_id": 14, "to_node_id": 26},
        {"id": 211, "from_node_id": 15, "to_node_id": 26},
        {"id": 212, "from_node_id": 16, "to_node_id": 25},
        {"id": 213, "from_node_id": 18, "to_node_id": 16},
        {"id": 214, "from_node_id": 19, "to_node_id": 16},
        {"id": 215, "from_node_id": 20, "to_node_id": 8},
        {"id": 216, "from_node_id": 21, "to_node_id": 8},
        {"id": 217, "from_node_id": 22, "to_node_id": 8},
        {"id": 218, "from_node_id": 23, "to_node_id": 16},
        {"id": 219, "from_node_id": 24, "to_node_id": 16},
    ]
    
    for c in connections:
        conn = Connection(id=c["id"], from_node_id=c["from_node_id"], to_node_id=c["to_node_id"])
        session.merge(conn)
    print(f"Added {len(connections)} connections")
    
    session.commit()
    session.close()
    print("Done!")

if __name__ == "__main__":
    seed()
