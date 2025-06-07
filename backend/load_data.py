import os
import chromadb
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

# --- Cấu hình ---
KNOWLEDGE_DIR = "data"
PERSIST_DIR = "db"
COLLECTION_NAME = "customer_service_qa"


def main():
    """
    Hàm chính để đọc, chia nhỏ dữ liệu từ các file .txt và nạp vào ChromaDB.
    """
    print("--- Bắt đầu quá trình nạp dữ liệu vào cơ sở tri thức ---")

    # 1. Khởi tạo ChromaDB client
    client = chromadb.PersistentClient(path=PERSIST_DIR)

    # 2. Tạo hoặc lấy collection
    print(f"Đang truy cập collection '{COLLECTION_NAME}'...")
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )
    print("=> Truy cập collection thành công.")

    # 3. THAY ĐỔI 1: Sử dụng Document Loaders của Langchain để đọc tất cả file
    if not os.path.exists(KNOWLEDGE_DIR):
        print(f"Lỗi: Thư mục '{KNOWLEDGE_DIR}' không tồn tại.")
        return

    print("\n--- Bắt đầu đọc và xử lý các file kiến thức ---")
    # Tự động tìm và đọc tất cả các file .txt trong thư mục
    loader = DirectoryLoader(
        KNOWLEDGE_DIR,
        glob="**/*.txt",
        loader_cls=TextLoader,
        loader_kwargs={'encoding': 'utf-8'}
    )
    documents = loader.load()

    if not documents:
        print("Cảnh báo: Không tìm thấy tài liệu nào để nạp.")
        return

    print(f"Đã tìm thấy {len(documents)} file trong thư mục '{KNOWLEDGE_DIR}'.")

    # 4. THAY ĐỔI 2: Chia nhỏ văn bản (Chunking)
    # Chia các tài liệu lớn thành các đoạn nhỏ hơn để tìm kiếm chính xác hơn
    print("\n--- Bắt đầu chia nhỏ tài liệu ---")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,  # Mỗi chunk có tối đa 1000 ký tự
        chunk_overlap=200  # Các chunk sẽ có 200 ký tự chồng lên nhau để không mất ngữ cảnh
    )
    chunks = text_splitter.split_documents(documents)
    print(f"=> Đã chia {len(documents)} tài liệu thành {len(chunks)} đoạn văn (chunks).")

    # 5. THAY ĐỔI 3: Nạp các chunks vào ChromaDB
    if chunks:
        print("\n--- Bắt đầu nạp dữ liệu (chunks) vào ChromaDB ---")
        ids = [f"chunk_{i}" for i in range(len(chunks))]  # Tạo ID duy nhất cho mỗi chunk

        # Lấy nội dung và metadata từ các chunks
        chunk_contents = [chunk.page_content for chunk in chunks]
        chunk_metadatas = [chunk.metadata for chunk in chunks]

        collection.add(
            documents=chunk_contents,
            metadatas=chunk_metadatas,
            ids=ids
        )
        print(f"\n=> Đã nạp thành công {len(chunks)} chunks vào cơ sở tri thức!")
    else:
        print("Không có chunks nào để nạp.")


if __name__ == '__main__':
    # Xóa thư mục DB cũ để đảm bảo dữ liệu mới được nạp sạch
    if os.path.exists(PERSIST_DIR):
        import shutil

        print(f"Đang xóa cơ sở dữ liệu cũ tại '{PERSIST_DIR}'...")
        shutil.rmtree(PERSIST_DIR)

    main()