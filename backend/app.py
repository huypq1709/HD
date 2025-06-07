from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
import chromadb
import os

# --- Cấu hình ứng dụng Flask ---
app = Flask(__name__)
CORS(app) 

# --- Cấu hình API Key của Google ---
try:
    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
except KeyError:
    print("Lỗi: Vui lòng thiết lập biến môi trường GOOGLE_API_KEY.")
    exit()

# --- Khởi tạo mô hình Gemini ---
model = genai.GenerativeModel('gemini-1.5-flash')

# --- Kết nối tới Cơ sở tri thức Vector (ChromaDB) ---
print("Đang kết nối tới cơ sở dữ liệu vector...")
try:
    client = chromadb.PersistentClient(path="db")
    collection = client.get_collection(name="customer_service_qa")
    print("=> Kết nối cơ sở dữ liệu thành công.")
except Exception as e:
    print(f"Lỗi: Không thể kết nối hoặc lấy collection từ ChromaDB. Hãy chắc chắn bạn đã chạy file 'load_data.py' trước. Chi tiết: {e}")
    exit()

# --- Hàm logic chính của Chatbot ---
def get_chatbot_response(user_query: str) -> str:
    """
    Hàm này nhận câu hỏi, tìm kiếm trong CSKT, và tạo câu trả lời.
    """
    print(f"\nNhận câu hỏi: '{user_query}'")
    results = collection.query(
        query_texts=[user_query],
        n_results=1
    )
    
    context_data = None
    distance = results['distances'][0][0] if results.get('distances') and results['distances'][0] else 1.0

    if distance < 0.6: 
         context_data = results['documents'][0][0]
         print(f"Tìm thấy thông tin liên quan (độ khác biệt: {distance:.2f})")
    else:
        print(f"Không tìm thấy thông tin đủ liên quan (độ khác biệt: {distance:.2f})")

    if context_data:
        # Trường hợp 1: TÌM THẤY -> Dùng RAG, yêu cầu Gemini chỉ trả lời dựa vào ngữ cảnh
        prompt = f"""Bạn là trợ lý ảo của HD Fitness and Yoga. Chỉ sử dụng thông tin được cung cấp trong phần \"THÔNG TIN THAM KHẢO\" để trả lời câu hỏi của khách hàng một cách thân thiện và chính xác. Không được suy diễn hay thêm thông tin ngoài lề.

        **THÔNG TIN THAM KHẢO:**
        "{context_data}"

        **Câu hỏi của khách hàng:**
        "{user_query}"

        **Câu trả lời của bạn:**
        """
        try:
            response = model.generate_content(prompt)
            print("=> Gemini đã tạo câu trả lời.")
            return response.text
        except Exception as e:
            print(f"Lỗi khi gọi Gemini API: {e}")
            return "Rất tiếc, đã có lỗi xảy ra trong quá trình xử lý. Vui lòng thử lại sau."
    else:
        # Trường hợp 2: KHÔNG TÌM THẤY -> Trả về câu trả lời cố định theo yêu cầu
        print("Không tìm thấy thông tin, trả về câu trả lời mặc định.")
        # Lấy thông tin liên hệ từ cơ sở kiến thức để câu trả lời được đầy đủ
        lien_he_results = collection.query(
            query_texts=["thông tin liên hệ hỗ trợ"],
            n_results=1
        )
        lien_he_info = lien_he_results['documents'][0][0] if lien_he_results['documents'] else "Zalo của trung tâm: HD fitness and yoga 033244646 hoặc hotline 0979764885."
        
        custom_response = f"Tôi chỉ là một mô hình chatbot AI bé nhỏ. Sếp tôi chưa cho tôi biết thông tin này. Vui lòng liên hệ sếp tôi theo các kênh sau nhé:\n\n{lien_he_info}"
        return custom_response


# --- Tạo Endpoint (địa chỉ) cho API ---
@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message')
    
    if not user_message:
        return jsonify({"error": "Không nhận được tin nhắn"}), 400
        
    bot_response = get_chatbot_response(user_message)
    
    return jsonify({"reply": bot_response})

# --- Chạy Server ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True) 