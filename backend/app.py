from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
import chromadb
import os
from langdetect import detect, LangDetectException
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- Cấu hình ứng dụng Flask ---
app = Flask(__name__)
CORS(app)

# --- Cấu hình API Key của Google ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in environment variables")

genai.configure(api_key=GOOGLE_API_KEY)

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

# --- Cấu hình câu trả lời mặc định ---
DEFAULT_RESPONSES = {
    'vi': {
        'greeting': "Chào bạn, tôi là trợ lý ảo của HD Fitness and Yoga. Tôi có thể giúp gì cho bạn?",
        'fallback': "Tôi chỉ là một mô hình chatbot AI bé nhỏ. Sếp tôi chưa cho tôi biết thông tin này. Vui lòng liên hệ sếp tôi theo các kênh sau nhé:\n\n"
    },
    'en': {
        'greeting': "Hello! I am the virtual assistant for HD Fitness and Yoga. How can I help you today?",
        'fallback': "I am just a small AI chatbot. My boss hasn't told me this information yet. Please contact my boss via the following channels:\n\n"
    }
}

CONTACT_INFO = {
    'vi': (
        "- Zalo chính thức: HD fitness and yoga, số 033244646\n"
        "- Hỗ trợ kỹ thuật: Zalo số 0971166684\n"
        "- Hotline khẩn cấp: 0979764885"
    ),
    'en': (
        "- Official Zalo: HD fitness and yoga, number 033244646\n"
        "- Technical Support: Zalo Mr. Huy, number 0971166684\n"
        "- Emergency Hotline: 0979764885"
    )
}

# --- Hàm logic chính của Chatbot ---
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
        lang = 'vi'

    # 2. Xử lý lời chào hỏi đơn giản
    greetings = {
        'vi': ["hi", "hello", "chào", "xin chào", "chào bạn", "chào shop", "alo"],
        'en': ["hi", "hello", "hey"]
    }
    
    if user_query_lower in greetings.get(lang, []):
        return DEFAULT_RESPONSES[lang]['greeting']

    # 3. Tìm kiếm thông tin trong cơ sở tri thức
    print("=> Tiến hành tìm kiếm RAG...")
    results = collection.query(
        query_texts=[user_query],
        n_results=3,
        include=["documents", "metadatas", "distances"]
    )

    context_data = None
    if results and results['documents'] and results['documents'][0]:
        # Lọc kết quả dựa trên khoảng cách (distance)
        valid_docs = []
        for doc, distance in zip(results['documents'][0], results['distances'][0]):
            if distance < 0.8:  # Chỉ lấy các kết quả có độ tương đồng cao
                valid_docs.append(doc)
        
        if valid_docs:
            context_data = "\n---\n".join(valid_docs)
            print(f"Tìm thấy {len(valid_docs)} đoạn văn bản phù hợp.")

    # 4. Tạo prompt và câu trả lời
    system_prompts = {
        'en': """You are a virtual assistant for HD Fitness and Yoga. Your task is to answer customer questions directly and accurately, based ONLY on the provided reference text.
- You MUST answer in English.
- Synthesize information from ALL reference text snippets to provide a complete answer.
- Do NOT ask questions back to the user. Get straight to the point.
- If the reference text doesn't contain enough information, say so clearly.""",
        
        'vi': """Bạn là một trợ lý ảo của HD Fitness and Yoga. Nhiệm vụ của bạn là trả lời câu hỏi của khách hàng một cách trực tiếp, chính xác, và đầy đủ nhất có thể, chỉ dựa vào tài liệu tham khảo được cung cấp.
- Bạn PHẢI trả lời bằng tiếng Việt.
- Tổng hợp thông tin từ TẤT CẢ các đoạn tài liệu tham khảo để đưa ra câu trả lời hoàn chỉnh.
- Nghiêm cấm đặt câu hỏi ngược lại cho người dùng.
- Trả lời thẳng vào vấn đề.
- Nếu tài liệu tham khảo không đủ thông tin, hãy nói rõ điều đó."""
    }

    if context_data:
        prompt = f"""{system_prompts[lang]}

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
            return DEFAULT_RESPONSES[lang]['fallback'] + CONTACT_INFO[lang]

    print("Không tìm thấy thông tin phù hợp, trả về câu trả lời mặc định.")
    return DEFAULT_RESPONSES[lang]['fallback'] + CONTACT_INFO[lang]

# --- Tạo Endpoint cho API ---
@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        if not data or 'message' not in data:
            return jsonify({"error": "Không nhận được tin nhắn"}), 400

        user_message = data['message']
        if not user_message.strip():
            return jsonify({"error": "Tin nhắn không được để trống"}), 400

        bot_response = get_chatbot_response(user_message)
        return jsonify({"reply": bot_response})

    except Exception as e:
        print(f"Lỗi xử lý request: {e}")
        return jsonify({"error": "Đã xảy ra lỗi khi xử lý yêu cầu"}), 500

# --- Chạy Server ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True) 