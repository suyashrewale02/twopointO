import re
from db.connection import get_connection

def tokenize(query):
    """Split query into words/tokens, removing punctuation and capitalizing."""
    words = re.findall(r'[a-zA-Z0-9]+', query)
    tokens = [word.capitalize() for word in words]
    return tokens

def main():
    """Loop that takes input from terminal and prints it."""
    print("\n=== Terminal Input Ready ===\n")
    print("Type your query and press Enter (type 'exit' to quit):\n")
    
    while True:
        try:
            query = input("Ask anything: ")
            if query.lower() == "exit":
                print("Exiting...")
                break
            tokens = tokenize(query)
            print(f"Tokens: {tokens}")
        except (EOFError, KeyboardInterrupt):
            print("\nExiting...")
            break

if __name__ == "__main__":
    main()
