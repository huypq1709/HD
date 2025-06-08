from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
import chromadb
import os
from langdetect import detect, LangDetectException

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
# Không cần system_instruction ở đây nữa, vì chúng ta sẽ đưa nó vào prompt động
model = genai.GenerativeModel('gemini-1.5-flash')

# --- Kết nối tới Cơ sở tri thức Vector (ChromaDB) ---
print("Đang kết nối tới cơ sở dữ liệu vector...")
try:
    client = chromadb.PersistentClient(path="db")
    collection = client.get_collection(name="customer_service_qa")
    print("=> Kết nối cơ sở dữ liệu thành công.")
except Exception as e:
    print(
        f"Lỗi: Không thể kết nối hoặc lấy collection từ ChromaDB. Hãy chắc chắn bạn đã chạy file 'load_data.py' trước. Chi tiết: {e}")
    exit()


# --- Hàm logic chính của Chatbot (PHIÊN BẢN ĐA NGÔN NGỮ) ---
def get_chatbot_response(user_query: str) -> str:
    """
    Hàm này nhận câu hỏi, phát hiện ngôn ngữ, tìm kiếm và tạo câu trả lời tương ứng.
    """
    print(f"\nNhận câu hỏi: '{user_query}'")
    user_query_lower = user_query.lower().strip()

    # 1. Phát hiện ngôn ngữ
    try:
        lang = detect(user_query)
        print(f"=> Ngôn ngữ được phát hiện: {lang}")
    except LangDetectException:
        print("=> Không phát hiện được ngôn ngữ, mặc định là tiếng Việt.")
        lang = 'vi'  # Mặc định là tiếng Việt nếu không phát hiện được

    # 2. Xử lý lời chào hỏi đơn giản
    greetings_vi = ["hi", "hello", "chào", "xin chào", "chào bạn", "chào shop", "alo"]
    greetings_en = ["hi", "hello", "hey"]
    if (lang == 'vi' and user_query_lower in greetings_vi) or \
            (lang == 'en' and user_query_lower in greetings_en):
        if lang == 'en':
            return "Hello! I am the virtual assistant for HD Fitness and Yoga. How can I help you today?"
        return "Chào bạn, tôi là trợ lý ảo của HD Fitness and Yoga. Tôi có thể giúp gì cho bạn?"

    # 3. Tìm kiếm thông tin trong cơ sở tri thức
    print("=> Tiến hành tìm kiếm RAG...")
    results = collection.query(query_texts=[user_query], n_results=3)

    context_data = None
    if results and results['documents'] and results['documents'][0]:
        context_data = "\n---\n".join(results['documents'][0])
        print(f"Tìm thấy ngữ cảnh, đưa cho Gemini xử lý.")

    # 4. Tạo prompt và câu trả lời mặc định dựa trên ngôn ngữ
    if lang == 'en':
        system_prompt = """You are a virtual assistant for HD Fitness and Yoga. Your task is to answer customer questions directly and accurately, based ONLY on the provided reference text.
- You MUST answer in English.
- Synthesize information from ALL reference text snippets to provide a complete answer.
- Do NOT ask questions back to the user. Get straight to the point.
"""
        default_response_text = "I am just a small AI chatbot. My boss hasn't told me this information yet. Please contact my boss via the following channels:\n\n"
        contact_info = (
            "- Official Zalo: HD fitness and yoga, number 033244646\n"
            "- Technical Support: Zalo, number 0971166684\n"
            "- Emergency Hotline: 0979764885"
        )
    else:  # Mặc định là tiếng Việt
        system_prompt = """Bạn là một trợ lý ảo của HD Fitness and Yoga. Nhiệm vụ của bạn là trả lời câu hỏi của khách hàng một cách trực tiếp, chính xác, và đầy đủ nhất có thể, chỉ dựa vào tài liệu tham khảo được cung cấp.
- Bạn PHẢI trả lời bằng tiếng Việt.
- Tổng hợp thông tin từ TẤT CẢ các đoạn tài liệu tham khảo để đưa ra câu trả lời hoàn chỉnh.
- Nghiêm cấm đặt câu hỏi ngược lại cho người dùng.
- Trả lời thẳng vào vấn đề.
"""
        default_response_text = "Tôi chỉ là một mô hình chatbot AI bé nhỏ. Sếp tôi chưa cho tôi biết thông tin này. Vui lòng liên hệ sếp tôi theo các kênh sau nhé:\n\n"
        contact_info = (
            "- Zalo chính thức: HD fitness and yoga, số 033244646\n"
            "- Hỗ trợ kỹ thuật: Zalo số 0971166684\n"
            "- Hotline khẩn cấp: 0979764885"
        )

    if context_data:
        prompt = f"""{system_prompt}

        **TÀI LIỆU THAM KHẢO:**
        {context_data}

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
            context_data = None

    if not context_data:
        print("Không tìm thấy thông tin, trả về câu trả lời mặc định.")
        return default_response_text + contact_info


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