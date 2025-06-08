# File: backend/check_db.py
import chromadb

print("--- Running ChromaDB Check ---")
try:
    client = chromadb.PersistentClient(path="db")
    print("Successfully connected to ChromaDB client.")

    collection = client.get_collection(name="customer_service_qa")
    print(f"Successfully got collection: '{collection.name}'")

    count = collection.count()
    print(f"Number of items in collection: {count}")

    if count > 0:
        print("\nAttempting to query for 'gym'...")
        results = collection.query(
            query_texts=["gym"],
            n_results=5,
            include=["documents", "distances"]
        )
        print("Query successful. Found results:")
        for i, (doc, dist) in enumerate(zip(results['documents'][0], results['distances'][0])):
            print(f"  - Result {i+1} (Distance: {dist:.4f}): \"{doc[:100]}...\"")
    else:
        print("\nCollection is empty. This is the reason chatbot cannot answer.")
        print("Please run 'load_data.py' again to populate the database.")

except Exception as e:
    print(f"\n!!! AN ERROR OCCURRED: {e}")
    print("This might be due to the collection not existing or a connection issue.")
    print("Please ensure 'load_data.py' has been run successfully.")

print("\n--- Check Complete ---")