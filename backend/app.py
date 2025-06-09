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

# --- Định nghĩa System Prompt cho các ngôn ngữ ---
# Đưa ra ngoài để dễ quản lý và tái sử dụng
VI_SYSTEM_PROMPT = """**Bối cảnh:** Bạn là một trợ lý ảo thông minh, thân thiện và có khả năng ghi nhớ ngữ cảnh của trung tâm "HD Fitness and Yoga".

**Nhiệm vụ:**
Dựa vào **LỊCH SỬ TRÒ CHUYỆN** và **TÀI LIỆU THAM KHẢO** được cung cấp để trả lời câu hỏi hiện tại của khách hàng một cách tự nhiên và chính xác.

**QUY TẮC XỬ LÝ:**
1.  **TẬN DỤNG NGỮ CẢNH:** Luôn xem xét các tin nhắn trước đó trong lịch sử để hiểu ý định của người dùng. Ví dụ, nếu người dùng đã nói "gym" và sau đó hỏi "giá", hãy tự hiểu là họ đang hỏi giá gym.
2.  **ƯU TIÊN TRẢ LỜI TRỰC TIẾP:** Cung cấp câu trả lời thẳng vào vấn đề.
3.  **TÌM KIẾM THÔNG TIN LIÊN QUAN:** Nếu không có câu trả lời trực tiếp, hãy cung cấp thông tin liên quan nhất có trong tài liệu.
4.  **KHI KHÔNG CÓ THÔNG TIN:** Chỉ khi tài liệu và lịch sử đều không có thông tin, hãy trả về chuỗi ký tự `NO_INFO_FOUND`.
5.  **NGÔN NGỮ:** Luôn trả lời bằng tiếng Việt.
"""

EN_SYSTEM_PROMPT = """**Your Role:** You are a smart, friendly, and stateful virtual assistant for "HD Fitness and Yoga" who remembers the conversation context.

**TASK:**
Use the **CONVERSATION HISTORY** and the provided **REFERENCE TEXT** to accurately and naturally answer the user's current question.

**PROCESSING RULES:**
1.  **USE CONTEXT:** Always review previous messages in the history to understand the user's intent. For example, if the user mentioned "gym" and then asks "what is the price?", understand they are asking for the gym price.
2.  **DIRECT ANSWERS FIRST:** Provide a direct answer to the question if possible.
3.  **FIND RELATED INFO:** If a direct answer isn't available, provide the most relevant information from the reference text.
4.  **WHEN NO INFO EXISTS:** Only if both the history and reference text lack information, return the exact string `NO_INFO_FOUND`.
5.  **LANGUAGE:** Always respond in English.
"""

# --- Khởi tạo các mô hình với System Prompt tương ứng ---
# Cách làm này giúp quản lý prompt sạch sẽ hơn
model_vi = genai.GenerativeModel('gemini-1.5-flash', system_instruction=VI_SYSTEM_PROMPT)
model_en = genai.GenerativeModel('gemini-1.5-flash', system_instruction=EN_SYSTEM_PROMPT)


def get_chatbot_response(user_query: str, history: list) -> str:
    print(f"\nNhận câu hỏi: '{user_query}'")
    print(f"Lịch sử có: {len(history)} tin nhắn")

    # 1. Phát hiện ngôn ngữ (đơn giản hóa, có thể cải thiện thêm nếu cần)
    lang = 'vi' # Mặc định là tiếng Việt
    try:
        if user_query:
            lang_detected = detect(user_query)
            if lang_detected != 'vi':
                lang = 'en'
    except LangDetectException:
        lang = 'en' # Nếu không chắc, ưu tiên tiếng Anh cho các từ ngắn
    
    print(f"=> Ngôn ngữ được xác định: {lang}")
    
    # 2. Chọn mô hình và thông tin liên hệ dựa trên ngôn ngữ
    if lang == 'en':
        model = model_en
        contact_info_text = (
            "I'm sorry, I don't have that specific information. "
            "For more details, please contact my human colleagues:\n\n"
            "- Official Zalo: HD fitness and yoga, number 033244646\n"
        )
    else:
        model = model_vi
        contact_info_text = (
            "Xin lỗi, tôi chưa có thông tin cụ thể về vấn đề này. "
            "Để biết chi tiết, bạn vui lòng liên hệ các đồng nghiệp của tôi qua Zalo 033244646 nhé."
        )

    # 3. Tìm kiếm thông tin trong cơ sở tri thức (RAG) DỰA TRÊN CÂU HỎI HIỆN TẠI
    print("=> Tiến hành tìm kiếm RAG cho câu hỏi hiện tại...")
    results = collection.query(query_texts=[user_query], n_results=5) 

    context_data = None
    if results and results['documents'] and results['documents'][0]:
        context_data = "\n---\n".join(results['documents'][0])
        print("=> Đã tìm thấy ngữ cảnh từ RAG.")
    
    # 4. Tạo prompt mới kết hợp RAG và câu hỏi hiện tại
    # AI sẽ dựa vào lịch sử trò chuyện và được cung cấp thêm ngữ cảnh RAG này
    final_prompt = f"""
**TÀI LIỆU THAM KHẢO BỔ SUNG (dựa trên câu hỏi hiện tại của bạn):**
---
{context_data if context_data else "Không có thông tin bổ sung."}
---

**Câu hỏi hiện tại của bạn:** "{user_query}"
"""

    # 5. Khởi tạo phiên chat với lịch sử và gửi prompt mới
    try:
        # Bắt đầu phiên chat với toàn bộ lịch sử trước đó
        chat_session = model.start_chat(history=history)
        
        # Gửi câu hỏi MỚI (đã được bổ sung ngữ cảnh RAG)
        response = chat_session.send_message(final_prompt)
        response_text = response.text.strip()
        print(f"=> Gemini đã trả lời: '{response_text}'")

        if "NO_INFO_FOUND" in response_text:
            print("=> Gemini không tìm thấy câu trả lời, hiển thị thông tin liên hệ.")
            return contact_info_text
        else:
            return response_text

    except Exception as e:
        print(f"Lỗi khi gọi Gemini API hoặc xử lý chat: {e}")
        return contact_info_text


# --- Cập nhật Endpoint API để nhận lịch sử ---
@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message')
    
    # NHẬN LỊCH SỬ TỪ REQUEST, nếu không có thì là list rỗng
    history = data.get('history', []) 

    if not user_message:
        return jsonify({"error": "Không nhận được tin nhắn"}), 400

    bot_response = get_chatbot_response(user_message, history)

    return jsonify({"reply": bot_response})


# --- Chạy Server ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)