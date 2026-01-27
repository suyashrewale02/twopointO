from core.traversal import traverse_node

def process_subject(results, classification):
    """Process tokens that are not control, operator, or subject."""
    excluded_types = {"control", "operator", "subject"}
    
    remaining = [r for r in results if r["node_type"] not in excluded_types]
    
    if remaining:
        print("\n--- Printing from subject ---")
        for r in remaining:
            print(f"  {r['label']}: {r['node_type']}, use_count={r['use_count']}")
            
            if classification == "instruction":
                traverse_node(r['label'])
    
    return remaining
