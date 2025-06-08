# File: backend/app.py (PHIÊN BẢN TỐI ƯU HÓA CHATBOT)

from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
import chromadb
import os
from langdetect import detect, LangDetectException
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
# Cấu hình CORS chặt chẽ hơn cho môi trường production
# Bạn cần thay 'http://3.0.181.201' bằng IP hoặc tên miền của bạn
CORS(app, resources={r"/api/*": {"origins": ["http://3.0.181.201", "http://localhost:5173"]}}) 

# --- Cấu hình API Key và các model ---
print("Attempting to configure backend...")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
model = None
collection = None
is_backend_ready = False
initialization_error = ""

try:
    if not GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY not found in environment variables. Please check your .env file on the server.")
    
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
    print(">>> Gemini model configured successfully.")

    print("Connecting to vector database...")
    client = chromadb.PersistentClient(path="db")
    collection = client.get_collection(name="customer_service_qa")
    print(">>> ChromaDB connection successful.")

    is_backend_ready = True
    print("✅ Chatbot backend is ready.")

except Exception as e:
    initialization_error = str(e)
    print(f"!!! CRITICAL STARTUP ERROR: {initialization_error}")


# --- Cấu hình câu trả lời mặc định ---
DEFAULT_RESPONSES = {
    'vi': {
        'greeting': "Chào bạn, tôi là trợ lý ảo của HD Fitness and Yoga. Tôi có thể giúp gì cho bạn?",
        'fallback': "Cảm ơn câu hỏi của bạn. Hiện tại tôi chưa được cung cấp thông tin chi tiết về vấn đề này. Để được hỗ trợ tốt nhất, bạn vui lòng liên hệ qua các kênh sau nhé:\n\n"
    },
    'en': {
        'greeting': "Hello! I am the virtual assistant for HD Fitness and Yoga. How can I help you today?",
        'fallback': "Thank you for your question. I don't have detailed information on this topic yet. For the best support, please contact us through the following channels:\n\n"
    }
}

CONTACT_INFO = {
    'vi': (
        "- **Zalo chính thức:** HD fitness and yoga (số 033244646)\n"
        "- **Hỗ trợ kỹ thuật (Zalo):** 0971166684\n"
        "- **Hotline khẩn cấp:** 0979764885"
    ),
    'en': (
        "- **Official Zalo:** HD fitness and yoga (number 033244646)\n"
        "- **Technical Support:** Zalo Mr. Huy (number 0971166684)\n"
        "- **Emergency Hotline:** 0979764885"
    )
}

# --- Hàm logic chính của Chatbot ---
def get_chatbot_response(user_query: str) -> str:
    print(f"\n[Chatbot] Nhận câu hỏi: '{user_query}'")
    user_query_lower = user_query.lower().strip()

    try:
        lang = detect(user_query)
        if lang not in ['vi', 'en']: lang = 'vi' # Mặc định là 'vi' nếu không phải en/vi
        print(f"[Chatbot] Ngôn ngữ được phát hiện: {lang}")
    except LangDetectException:
        print("[Chatbot] Không phát hiện được ngôn ngữ, mặc định là tiếng Việt.")
        lang = 'vi'

    greetings = {
        'vi': ["hi", "hello", "chào", "xin chào", "chào bạn", "chào shop", "alo"],
        'en': ["hi", "hello", "hey"]
    }
    
    if user_query_lower in greetings.get(lang, []):
        return DEFAULT_RESPONSES[lang]['greeting']

    print("[Chatbot] Tiến hành tìm kiếm trong cơ sở tri thức (RAG)...")
    try:
        results = collection.query(
            query_texts=[user_query],
            n_results=3, # Lấy 3 kết quả liên quan nhất
            include=["documents", "metadatas", "distances"]
        )
    except Exception as e:
        print(f"!!! LỖI khi query ChromaDB: {e}")
        return DEFAULT_RESPONSES[lang]['fallback'] + CONTACT_INFO[lang]

    context_data = None
    if results and results['documents'] and results['documents'][0]:
        print("[Chatbot] Các kết quả tìm được (distance càng nhỏ càng liên quan):")
        for i, (doc, dist) in enumerate(zip(results['documents'][0], results['distances'][0])):
            print(f"  - Kết quả {i+1} (Distance: {dist:.4f}): \"{doc[:80]}...\"")

        # Ngưỡng chấp nhận kết quả
        distance_threshold = 1.0 
        valid_docs = [
            doc for doc, dist in zip(results['documents'][0], results['distances'][0]) 
            if dist < distance_threshold
        ]
        
        if valid_docs:
            context_data = "\n---\n".join(valid_docs)
            print(f"[Chatbot] Tìm thấy {len(valid_docs)} đoạn văn bản hợp lệ (distance < {distance_threshold}).")
        else:
            print("[Chatbot] Không có đoạn văn bản nào đủ liên quan (dưới ngưỡng distance).")

    system_prompt = f"""Bạn là một trợ lý ảo chuyên nghiệp và thân thiện của trung tâm "HD Fitness and Yoga".
- Trả lời câu hỏi của khách hàng một cách ngắn gọn, đi thẳng vào vấn đề, và CHỈ DỰA VÀO "TÀI LIỆU THAM KHẢO" được cung cấp.
- PHẢI trả lời bằng {'tiếng Việt' if lang == 'vi' else 'English'}.
- Không tự bịa đặt thông tin.
- Nếu tài liệu không chứa câu trả lời, hãy nói rõ rằng bạn chưa có thông tin này và hướng dẫn khách liên hệ các kênh hỗ trợ được cung cấp trong TÀI LIỆU THAM KHẢO.
- Trình bày câu trả lời rõ ràng, dùng gạch đầu dòng nếu cần.
"""

    if context_data:
        prompt = f"""{system_prompt}\n\n**TÀI LIỆU THAM KHẢO:**\n{context_data}\n\n**Câu hỏi của khách hàng:**\n"{user_query}"\n\n**Câu trả lời của bạn:**"""
        try:
            print("[Chatbot] Gửi prompt đến Gemini...")
            response = model.generate_content(prompt)
            print("[Chatbot] Gemini đã tạo câu trả lời.")
            return response.text
        except Exception as e:
            print(f"!!! LỖI khi gọi Gemini API: {e}")
            return DEFAULT_RESPONSES[lang]['fallback'] + CONTACT_INFO[lang]

    print("[Chatbot] Không tìm thấy thông tin phù hợp, trả về câu trả lời mặc định.")
    return DEFAULT_RESPONSES[lang]['fallback'] + CONTACT_INFO[lang]

@app.route('/chat', methods=['POST'])
def chat():
    if not is_backend_ready:
        return jsonify({"error": f"Chatbot service is not available due to: {initialization_error}"}), 503

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
        print(f"[API /chat] Lỗi xử lý request: {e}")
        return jsonify({"error": "Đã xảy ra lỗi khi xử lý yêu cầu của bạn."}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5009))
    app.run(host='0.0.0.0', port=port, debug=False)