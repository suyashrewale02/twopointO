from core.tokenizer import tokenize
from core.detection import detect_tokens, classify_query
from core.subject import process_subject

def run_query_loop():
    """Loop that takes input from terminal and prints results."""
    print("\n=== Terminal Input Ready ===\n")
    print("Type your query and press Enter (type 'exit' to quit):\n")
    
    while True:
        try:
            query = input("-----------------------------\nAsk anything: ")
            if query.lower() == "exit":
                print("Exiting...")
                break
            
            tokens = tokenize(query)
            print(f"\nTokens: {tokens}")
            results = detect_tokens(tokens)
            
            # Print only control, operator, subject
            detection_types = {"control", "operator", "subject"}
            for result in results:
                if result["node_type"] in detection_types:
                    print(f"  {result['label']}: {result['node_type']}, use_count={result['use_count']}")
            
            classification = classify_query(results)
            print(f"\n{classification}")
            
            # Print rest in subject
            process_subject(results, classification)
            
        except (EOFError, KeyboardInterrupt):
            print("\nExiting...")
            break
