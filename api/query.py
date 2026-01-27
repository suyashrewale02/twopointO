from core.tokenizer import tokenize
from core.detection import detect_tokens, classify_query

def run_query_loop():
    """Loop that takes input from terminal and prints results."""
    print("\n=== Terminal Input Ready ===\n")
    print("Type your query and press Enter (type 'exit' to quit):\n")
    
    while True:
        try:
            query = input("Ask anything: ")
            if query.lower() == "exit":
                print("Exiting...")
                break
            
            tokens = tokenize(query)
            results = detect_tokens(tokens)
            
            for result in results:
                print(f"  {result['label']}: {result['node_type']}")
            
            classification = classify_query(results)
            print(f"\n{classification}")
            
        except (EOFError, KeyboardInterrupt):
            print("\nExiting...")
            break
