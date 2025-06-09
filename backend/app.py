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


# --- Hàm logic chính của Chatbot ---
def get_chatbot_response(user_query: str) -> str:
    print(f"\nNhận câu hỏi: '{user_query}'")
    user_query_lower = user_query.lower().strip()

    # 1. Phát hiện ngôn ngữ
    try:
        # Tăng cường nhận diện: Nếu câu quá ngắn, khó xác định, ưu tiên tiếng Anh
        if len(user_query_lower.split()) < 3:
             # Các từ ngắn phổ biến của tiếng Việt
            vietnamese_short_words = ["giá", "vé", "tập", "gym", "yoga", "hỏi", "có", "không"]
            if any(word in user_query_lower for word in vietnamese_short_words):
                 lang = 'vi'
            else:
                 lang = detect(user_query)
        else:
            lang = detect(user_query)

        # Mặc định là tiếng Anh nếu không phải 'vi'
        if lang != 'vi':
            lang = 'en'
            
        print(f"=> Ngôn ngữ được xác định: {lang}")
    except LangDetectException:
        print("=> Không phát hiện được ngôn ngữ, mặc định là tiếng Anh.")
        lang = 'en'

    # 2. Xử lý lời chào hỏi đơn giản
    greetings_vi = ["chào", "xin chào", "chào bạn", "chào shop", "alo"]
    greetings_en = ["hi", "hello", "hey", "yo"]
    if user_query_lower in greetings_vi:
        lang = 'vi'
    elif user_query_lower in greetings_en:
        lang = 'en'

    if lang == 'vi' and user_query_lower in greetings_vi:
        return "Chào bạn, tôi là trợ lý ảo của HD Fitness and Yoga. Tôi có thể giúp gì cho bạn?"
    if lang == 'en' and user_query_lower in greetings_en:
        return "Hello! I am the virtual assistant for HD Fitness and Yoga. How can I help you today?"


    # 3. Tìm kiếm thông tin trong cơ sở tri thức
    print("=> Tiến hành tìm kiếm RAG...")
    results = collection.query(query_texts=[user_query], n_results=7) 

    context_data = None
    if results and results['documents'] and results['documents'][0]:
        context_data = "\n---\n".join(results['documents'][0])
        print("Tìm thấy ngữ cảnh, bắt đầu tạo prompt cho Gemini.")

    # 4. Tạo prompt và định nghĩa các kênh liên hệ
    # *** BẮT ĐẦU CẬP NHẬT LOGIC VÀ PROMPT ***
    if lang == 'en':
        system_prompt = """**Your Role:** You are a helpful, smart assistant for "HD Fitness and Yoga".

**RULE #1: LANGUAGE IS CRITICAL.**
- The user is asking in English.
- You **MUST** write your entire response in **English**. No exceptions.

**TASK:**
- Understand the user's question.
- Based **ONLY** on the **REFERENCE TEXT** provided, answer the question.
- If the question is generic (e.g., "price", "info"), and the text has multiple prices (gym, yoga), ask for clarification.
- If the text has **no relevant information** to answer the question, you **MUST** return the exact string: `NO_INFO_FOUND`.
"""
        contact_info_text = (
            "I'm sorry, I don't have that specific information. "
            "For more details, please contact my human colleagues:\n\n"
            "- Official Zalo: HD fitness and yoga, number 033244646\n"
            "- Technical Support (Zalo): 0971166684\n"
            "- Emergency Hotline: 0979764885"
        )
    else:  # Mặc định là tiếng Việt
        system_prompt = """**Bối cảnh:** Bạn là một trợ lý ảo thông minh và linh hoạt của trung tâm "HD Fitness and Yoga".

**QUY TẮC SỐ 1: NGÔN NGỮ LÀ QUAN TRỌNG NHẤT.**
- Khách hàng đang hỏi bằng tiếng Việt.
- Bạn **BẮT BUỘC** phải viết toàn bộ câu trả lời bằng **tiếng Việt**.

**Nhiệm vụ:**
- Hiểu rõ câu hỏi của khách hàng.
- Chỉ dựa vào **TÀI LIỆU THAM KHẢO** được cung cấp để trả lời.
- Nếu câu hỏi quá chung chung (ví dụ: "giá", "thông tin"), và tài liệu có nhiều loại giá (gym, yoga), hãy hỏi lại để làm rõ.
- Nếu tài liệu **hoàn toàn không chứa thông tin** liên quan, bạn **BẮT BUỘC** phải trả về chuỗi ký tự `NO_INFO_FOUND`.
"""
        contact_info_text = (
            "Xin lỗi, tôi chưa có thông tin cụ thể về vấn đề này. "
            "Để biết chi tiết, bạn vui lòng liên hệ các đồng nghiệp của tôi qua các kênh sau nhé:\n\n"
            "- Zalo chính thức: HD fitness and yoga, số 033244646\n"
            "- Hỗ trợ kỹ thuật: Zalo số 0971166684\n"
            "- Hotline khẩn cấp: 0979764885"
        )

    # Nếu không tìm thấy ngữ cảnh nào, trả về thông tin liên hệ ngay
    if not context_data:
        print("Không tìm thấy ngữ cảnh nào trong DB, trả về thông tin liên hệ.")
        return contact_info_text

    # Nếu có ngữ cảnh, đưa cho AI xử lý
    prompt = f"""{system_prompt}

**REFERENCE TEXT:**
---
{context_data}
---

**User's question:** "{user_query}"

**Your Answer:**
"""
    try:
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        print(f"=> Gemini đã trả lời: '{response_text}'")

        # Kiểm tra xem AI có trả về mã đặc biệt không
        if "NO_INFO_FOUND" in response_text:
            print("=> Gemini không tìm thấy câu trả lời, hiển thị thông tin liên hệ.")
            return contact_info_text
        else:
            # Nếu có câu trả lời, trả về cho người dùng
            return response_text

    except Exception as e:
        print(f"Lỗi khi gọi Gemini API: {e}")
        # Nếu có lỗi xảy ra với API, cũng trả về thông tin liên hệ
        return contact_info_text

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