import os
import chromadb
# THAY ĐỔI: Thêm MarkdownHeaderTextSplitter
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter, MarkdownHeaderTextSplitter

# --- Cấu hình ---
KNOWLEDGE_DIR = "data"
PERSIST_DIR = "db"
COLLECTION_NAME = "customer_service_qa"


def main():
    """
    Hàm chính để đọc, chia nhỏ dữ liệu từ các file .md và nạp vào ChromaDB.
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

    # 3. Đọc tất cả file .md
    if not os.path.exists(KNOWLEDGE_DIR):
        print(f"Lỗi: Thư mục '{KNOWLEDGE_DIR}' không tồn tại.")
        return

    print("\n--- Bắt đầu đọc và xử lý các file kiến thức ---")
    loader = DirectoryLoader(
        KNOWLEDGE_DIR,
        # *** THAY ĐỔI TẠI ĐÂY: Đọc file .md thay vì .txt ***
        glob="**/*.md", 
        loader_cls=TextLoader,
        loader_kwargs={'encoding': 'utf-8'}
    )
    documents = loader.load()

    if not documents:
        print("Cảnh báo: Không tìm thấy tài liệu nào để nạp.")
        return

    print(f"Đã tìm thấy {len(documents)} file trong thư mục '{KNOWLEDGE_DIR}'.")

    # 4. Chia nhỏ văn bản (Chunking) theo cấu trúc Markdown
    print("\n--- Bắt đầu chia nhỏ tài liệu theo cấu trúc Markdown ---")
    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
    ]
    markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
    
    # Vì loader trả về list documents, ta xử lý từng cái một
    md_header_splits = []
    for doc in documents:
        md_header_splits.extend(markdown_splitter.split_text(doc.page_content))

    # Chia nhỏ thêm nếu các chunk vẫn còn quá lớn
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100
    )
    chunks = text_splitter.split_documents(md_header_splits)
    print(f"=> Đã chia {len(documents)} tài liệu thành {len(chunks)} đoạn văn (chunks).")

    # 5. Nạp các chunks vào ChromaDB
    if chunks:
        print("\n--- Bắt đầu nạp dữ liệu (chunks) vào ChromaDB ---")
        ids = [f"chunk_{i}" for i in range(len(chunks))]
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
    if os.path.exists(PERSIST_DIR):
        import shutil
        print(f"Đang xóa cơ sở dữ liệu cũ tại '{PERSIST_DIR}'...")
        shutil.rmtree(PERSIST_DIR)
    main()