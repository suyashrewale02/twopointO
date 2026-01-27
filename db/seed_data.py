from db.connection import get_session, Node, Connection

def seed():
    session = get_session()
    
    # New nodes
    nodes = [
  {"id":28, "label":"fruit", "node_type":"abstraction", "created_at":"2026-01-28T10:00:00Z", "last_used_at":"2026-01-28T10:00:00Z", "use_count":10},
  {"id":29, "label":"tree", "node_type":"perceptual", "created_at":"2026-01-28T10:01:00Z", "last_used_at":"2026-01-28T10:01:00Z", "use_count":9},
  {"id":30, "label":"red", "node_type":"perceptual", "created_at":"2026-01-28T10:02:00Z", "last_used_at":"2026-01-28T10:02:00Z", "use_count":8},
  {"id":31, "label":"round", "node_type":"perceptual", "created_at":"2026-01-28T10:03:00Z", "last_used_at":"2026-01-28T10:03:00Z", "use_count":7},
  {"id":32, "label":"eat", "node_type":"action", "created_at":"2026-01-28T10:04:00Z", "last_used_at":"2026-01-28T10:04:00Z", "use_count":6},

  {"id":33, "label":"color", "node_type":"abstraction", "created_at":"2026-01-28T10:05:00Z", "last_used_at":"2026-01-28T10:05:00Z", "use_count":5},
  {"id":34, "label":"taste", "node_type":"perceptual", "created_at":"2026-01-28T10:06:00Z", "last_used_at":"2026-01-28T10:06:00Z", "use_count":5},
  {"id":35, "label":"plant type", "node_type":"abstraction", "created_at":"2026-01-28T10:07:00Z", "last_used_at":"2026-01-28T10:07:00Z", "use_count":4},
  {"id":36, "label":"round shape", "node_type":"perceptual", "created_at":"2026-01-28T10:08:00Z", "last_used_at":"2026-01-28T10:08:00Z", "use_count":4},
  {"id":37, "label":"ripeness", "node_type":"perceptual", "created_at":"2026-01-28T10:09:00Z", "last_used_at":"2026-01-28T10:09:00Z", "use_count":4},

  {"id":38, "label":"yellow", "node_type":"perceptual", "created_at":"2026-01-28T10:10:00Z", "last_used_at":"2026-01-28T10:10:00Z", "use_count":3},
  {"id":39, "label":"sweet", "node_type":"perceptual", "created_at":"2026-01-28T10:11:00Z", "last_used_at":"2026-01-28T10:11:00Z", "use_count":3},
  {"id":40, "label":"planting season", "node_type":"abstraction", "created_at":"2026-01-28T10:12:00Z", "last_used_at":"2026-01-28T10:12:00Z", "use_count":2},
  {"id":41, "label":"grows in orchard", "node_type":"perceptual", "created_at":"2026-01-28T10:13:00Z", "last_used_at":"2026-01-28T10:13:00Z", "use_count":2},
  {"id":42, "label":"round curve", "node_type":"perceptual", "created_at":"2026-01-28T10:14:00Z", "last_used_at":"2026-01-28T10:14:00Z", "use_count":2},

  {"id":43, "label":"tree type", "node_type":"abstraction", "created_at":"2026-01-28T10:15:00Z", "last_used_at":"2026-01-28T10:15:00Z", "use_count":2},
  {"id":44, "label":"branch", "node_type":"perceptual", "created_at":"2026-01-28T10:16:00Z", "last_used_at":"2026-01-28T10:16:00Z", "use_count":2},
  {"id":45, "label":"leaf", "node_type":"perceptual", "created_at":"2026-01-28T10:17:00Z", "last_used_at":"2026-01-28T10:17:00Z", "use_count":2},

  {"id":46, "label":"bite", "node_type":"action", "created_at":"2026-01-28T10:18:00Z", "last_used_at":"2026-01-28T10:18:00Z", "use_count":2},
  {"id":47, "label":"cook", "node_type":"action", "created_at":"2026-01-28T10:19:00Z", "last_used_at":"2026-01-28T10:19:00Z", "use_count":1},
  {"id":48, "label":"dessert", "node_type":"abstraction", "created_at":"2026-01-28T10:20:00Z", "last_used_at":"2026-01-28T10:20:00Z", "use_count":1},

  {"id":49, "label":"ripe", "node_type":"perceptual", "created_at":"2026-01-28T10:21:00Z", "last_used_at":"2026-01-28T10:21:00Z", "use_count":1},
  {"id":50, "label":"unripe", "node_type":"perceptual", "created_at":"2026-01-28T10:22:00Z", "last_used_at":"2026-01-28T10:22:00Z", "use_count":1},

  {"id":51, "label":"farm", "node_type":"perceptual", "created_at":"2026-01-28T10:23:00Z", "last_used_at":"2026-01-28T10:23:00Z", "use_count":1},
  {"id":52, "label":"season", "node_type":"abstraction", "created_at":"2026-01-28T10:24:00Z", "last_used_at":"2026-01-28T10:24:00Z", "use_count":1},

  {"id":53, "label":"cook method", "node_type":"abstraction", "created_at":"2026-01-28T10:25:00Z", "last_used_at":"2026-01-28T10:25:00Z", "use_count":1},
  {"id":54, "label":"baked", "node_type":"action", "created_at":"2026-01-28T10:26:00Z", "last_used_at":"2026-01-28T10:26:00Z", "use_count":1},
  {"id":55, "label":"juice", "node_type":"abstraction", "created_at":"2026-01-28T10:27:00Z", "last_used_at":"2026-01-28T10:27:00Z", "use_count":1},
  
  {"id":56, "label":"circle", "node_type":"perceptual", "created_at":"2026-01-28T10:28:00Z", "last_used_at":"2026-01-28T10:28:00Z", "use_count":1},
  {"id":57, "label":"shape", "node_type":"abstraction", "created_at":"2026-01-28T10:29:00Z", "last_used_at":"2026-01-28T10:29:00Z", "use_count":1},
]

    
    for n in nodes:
        node = Node(id=n["id"], label=n["label"], node_type=n["node_type"])
        session.merge(node)
    print(f"Added {len(nodes)} nodes")
    
    # New connections
    connections = [
  {"id":220, "from_node_id":1, "to_node_id":28, "relation_strength":0.92, "use_count":10, "last_used_at":"2026-01-28T10:00:00Z"},
  {"id":221, "from_node_id":1, "to_node_id":29, "relation_strength":0.75, "use_count":9, "last_used_at":"2026-01-28T10:01:00Z"},
  {"id":222, "from_node_id":1, "to_node_id":30, "relation_strength":0.88, "use_count":8, "last_used_at":"2026-01-28T10:02:00Z"},
  {"id":223, "from_node_id":1, "to_node_id":31, "relation_strength":0.6, "use_count":7, "last_used_at":"2026-01-28T10:03:00Z"},
  {"id":224, "from_node_id":1, "to_node_id":32, "relation_strength":0.85, "use_count":6, "last_used_at":"2026-01-28T10:04:00Z"},

  {"id":225, "from_node_id":30, "to_node_id":33, "relation_strength":0.95, "use_count":5, "last_used_at":"2026-01-28T10:05:00Z"},
  {"id":226, "from_node_id":32, "to_node_id":34, "relation_strength":0.9, "use_count":5, "last_used_at":"2026-01-28T10:06:00Z"},
  {"id":227, "from_node_id":29, "to_node_id":35, "relation_strength":0.85, "use_count":4, "last_used_at":"2026-01-28T10:07:00Z"},
  {"id":228, "from_node_id":31, "to_node_id":36, "relation_strength":0.88, "use_count":4, "last_used_at":"2026-01-28T10:08:00Z"},
  {"id":229, "from_node_id":31, "to_node_id":37, "relation_strength":0.8, "use_count":4, "last_used_at":"2026-01-28T10:09:00Z"},

  {"id":230, "from_node_id":28, "to_node_id":38, "relation_strength":0.9, "use_count":3, "last_used_at":"2026-01-28T10:10:00Z"},
  {"id":231, "from_node_id":28, "to_node_id":39, "relation_strength":0.92, "use_count":3, "last_used_at":"2026-01-28T10:11:00Z"},
  {"id":232, "from_node_id":28, "to_node_id":40, "relation_strength":0.8, "use_count":2, "last_used_at":"2026-01-28T10:12:00Z"},
  {"id":233, "from_node_id":29, "to_node_id":41, "relation_strength":0.75, "use_count":2, "last_used_at":"2026-01-28T10:13:00Z"},
  {"id":234, "from_node_id":29, "to_node_id":42, "relation_strength":0.7, "use_count":2, "last_used_at":"2026-01-28T10:14:00Z"},

  {"id":235, "from_node_id":29, "to_node_id":43, "relation_strength":0.72, "use_count":2, "last_used_at":"2026-01-28T10:15:00Z"},
  {"id":236, "from_node_id":29, "to_node_id":44, "relation_strength":0.68, "use_count":2, "last_used_at":"2026-01-28T10:16:00Z"},
  {"id":237, "from_node_id":29, "to_node_id":45, "relation_strength":0.7, "use_count":2, "last_used_at":"2026-01-28T10:17:00Z"},

  {"id":238, "from_node_id":32, "to_node_id":46, "relation_strength":0.85, "use_count":2, "last_used_at":"2026-01-28T10:18:00Z"},
  {"id":239, "from_node_id":32, "to_node_id":45, "relation_strength":0.8, "use_count":1, "last_used_at":"2026-01-28T10:19:00Z"},
  {"id":240, "from_node_id":32, "to_node_id":46, "relation_strength":0.7, "use_count":1, "last_used_at":"2026-01-28T10:20:00Z"},

  {"id":241, "from_node_id":37, "to_node_id":47, "relation_strength":0.85, "use_count":1, "last_used_at":"2026-01-28T10:21:00Z"},
  {"id":242, "from_node_id":37, "to_node_id":48, "relation_strength":0.7, "use_count":1, "last_used_at":"2026-01-28T10:22:00Z"},

  {"id":243, "from_node_id":41, "to_node_id":49, "relation_strength":0.7, "use_count":1, "last_used_at":"2026-01-28T10:23:00Z"},
  {"id":244, "from_node_id":40, "to_node_id":50, "relation_strength":0.6, "use_count":1, "last_used_at":"2026-01-28T10:24:00Z"},

  {"id":245, "from_node_id":45, "to_node_id":45, "relation_strength":0.6, "use_count":1, "last_used_at":"2026-01-28T10:25:00Z"},
  {"id":246, "from_node_id":45, "to_node_id":50, "relation_strength":0.8, "use_count":1, "last_used_at":"2026-01-28T10:26:00Z"},
  {"id":247, "from_node_id":45, "to_node_id":51, "relation_strength":0.7, "use_count":1, "last_used_at":"2026-01-28T10:27:00Z"},

  {"id":248, "from_node_id":36, "to_node_id":56, "relation_strength":0.9, "use_count":1, "last_used_at":"2026-01-28T10:28:00Z"},
  {"id":249, "from_node_id":36, "to_node_id":57, "relation_strength":0.8, "use_count":1, "last_used_at":"2026-01-28T10:29:00Z"},
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
