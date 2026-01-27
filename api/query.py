from core.tokenizer import tokenize
from core.detection import detect_tokens

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
            print(f"\nTokens: {tokens}\n")
            
            results = detect_tokens(tokens)
            for result in results:
                print(f"  {result['label']}: node_type={result['node_type']}, use_count={result['use_count']}")
            print()
            
        except (EOFError, KeyboardInterrupt):
            print("\nExiting...")
            break
