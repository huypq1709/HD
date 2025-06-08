# File: backend/preload_models.py
import chromadb
import os

# Chỉ cần chạy khi không ở trong môi trường test (nếu bạn có)
if os.getenv("CI") != "true":
    print("Preloading ChromaDB embedding models...")
    try:
        # Dòng này sẽ kích hoạt việc tải model nếu nó chưa tồn tại
        client = chromadb.PersistentClient(path="db")
        # get_or_create_collection sẽ tạo nếu chưa có, và tải model nếu cần
        collection = client.get_or_create_collection(name="customer_service_qa")
        print(f"Collection '{collection.name}' is ready. Model preloading seems complete.")
        # Thêm một query nhỏ để đảm bảo model được load vào bộ nhớ
        collection.query(query_texts=["test"], n_results=1)
        print("Initial query successful. Models are loaded.")
    except Exception as e:
        print(f"An error occurred during model preloading: {e}")
        # Không exit, chỉ in lỗi, để build có thể tiếp tục