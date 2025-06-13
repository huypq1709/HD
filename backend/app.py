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
VI_SYSTEM_PROMPT = """**Bối cảnh:** Bạn là một trợ lý ảo thông minh, có khả năng ghi nhớ ngữ cảnh của trung tâm "HD Fitness and Yoga".

**QUY TẮC TỐI THƯỢNG: TỔNG HỢP ĐỂ HOÀN CHỈNH**
Nhiệm vụ quan trọng nhất của bạn là **tổng hợp thông tin từ TẤT CẢ các đoạn TÀI LIỆU THAM KHẢO** được cung cấp để tạo ra một câu trả lời đầy đủ và hoàn chỉnh nhất có thể. Đừng chỉ dừng lại ở một mảnh thông tin.

**QUY TẮC XỬ LÝ:**
1.  **TẬN DỤNG NGỮ CẢNH:** Luôn xem xét **LỊCH SỬ TRÒ CHUYỆN** để hiểu ý định của người dùng.
2.  **TỔNG HỢP THÔNG TIN:** Khi trả lời, hãy kết hợp các chi tiết từ nhiều đoạn tài liệu khác nhau nếu cần. Ví dụ, nếu người dùng hỏi về "giá khuyến mãi", bạn phải tìm thông tin chung về chương trình khuyến mãi VÀ tìm cả các bảng giá chi tiết cho từng nhóm khách hàng để trình bày đầy đủ.
3.  **HỎI LẠI KHI CẦN:** Nếu câu hỏi không rõ ràng (ví dụ: "giá bao nhiêu?") và tài liệu có nhiều loại giá, hãy hỏi lại để làm rõ họ muốn biết giá cho đối tượng nào (Học sinh, khách mới, hay khách cũ?).
4.  **KHI KHÔNG CÓ THÔNG TIN:** Chỉ khi đã xem xét tất cả tài liệu mà vẫn không có thông tin, hãy trả về chuỗi ký tự `NO_INFO_FOUND`.
5.  **NGÔN NGỮ:** Luôn trả lời bằng tiếng Việt.
"""

EN_SYSTEM_PROMPT = """**Your Role:** You are a smart, context-aware virtual assistant for "HD Fitness and Yoga".

**THE ULTIMATE RULE: SYNTHESIZE FOR COMPLETENESS**
Your most important task is to **synthesize information from ALL provided REFERENCE TEXT snippets** to create the most complete and comprehensive answer possible. Do not stop at the first piece of information you find.

**PROCESSING RULES:**
1.  **USE CONTEXT:** Always review the **CONVERSATION HISTORY** to understand the user's intent.
2.  **SYNTHESIZE INFORMATION:** When answering, combine details from different text snippets if necessary. For example, if the user asks about "promotional price", you must find general info about the promotion AND find the detailed price lists for each customer group to provide a full answer.
3.  **ASK FOR CLARIFICATION:** If a question is ambiguous (e.g., "what's the price?") and the text contains multiple prices, ask the user to clarify which group they belong to (Student, New, or Returning Customer?).
4.  **WHEN NO INFO EXISTS:** Only after reviewing all documents and finding no relevant info, return the exact string `NO_INFO_FOUND`.
5.  **LANGUAGE:** Always respond in English.
"""

# --- Khởi tạo các mô hình với System Prompt tương ứng ---
model_vi = genai.GenerativeModel('gemini-1.5-flash', system_instruction=VI_SYSTEM_PROMPT)
model_en = genai.GenerativeModel('gemini-1.5-flash', system_instruction=EN_SYSTEM_PROMPT)


def get_chatbot_response(user_query: str, history: list) -> str:
    print(f"\nNhận câu hỏi: '{user_query}'")
    print(f"Lịch sử có: {len(history)} tin nhắn")

    # 1. Phát hiện ngôn ngữ
    lang = 'vi'
    try:
        if user_query:
            lang_detected = detect(user_query)
            if lang_detected != 'vi':
                lang = 'en'
    except LangDetectException:
        lang = 'en'
    
    print(f"=> Ngôn ngữ được xác định: {lang}")
    
    # 2. Chọn mô hình và thông tin liên hệ
    if lang == 'en':
        model = model_en
        contact_info_text = "I'm sorry, I couldn't find detailed information on that. For more specifics, please contact my human colleagues via Zalo at 033244646."
    else:
        model = model_vi
        contact_info_text = "Xin lỗi, tôi không tìm thấy thông tin chi tiết về vấn đề này. Để biết cụ thể hơn, bạn vui lòng liên hệ các đồng nghiệp của tôi qua Zalo 033244646 nhé."

    # 3. Tìm kiếm thông tin trong cơ sở tri thức (RAG)
    print("=> Tiến hành tìm kiếm RAG...")
    # Tăng số lượng kết quả để có cơ hội lấy được tất cả các phần liên quan của chương trình khuyến mãi
    results = collection.query(query_texts=[user_query], n_results=10) 

    context_data = None
    if results and results['documents'] and results['documents'][0]:
        # Dùng set để loại bỏ các chunk trùng lặp trước khi join
        unique_docs = list(dict.fromkeys(results['documents'][0]))
        context_data = "\n---\n".join(unique_docs)
        print("=> Đã tìm thấy ngữ cảnh từ RAG.")
    
    # 4. Tạo prompt cuối cùng
    final_prompt = f"""
**TÀI LIỆU THAM KHẢO BỔ SUNG (dựa trên câu hỏi hiện tại của bạn):**
---
{context_data if context_data else "Không có thông tin bổ sung."}
---

**Câu hỏi hiện tại của bạn:** "{user_query}"
"""

    # 5. Khởi tạo phiên chat và gửi prompt
    try:
        chat_session = model.start_chat(history=history)
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


# --- Endpoint API ---
@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message')
    history = data.get('history', []) 

    if not user_message:
        return jsonify({"error": "Không nhận được tin nhắn"}), 400

    bot_response = get_chatbot_response(user_message, history)

    return jsonify({"reply": bot_response})


# --- Chạy Server ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)