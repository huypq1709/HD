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
        lang = detect(user_query)
        print(f"=> Ngôn ngữ được phát hiện: {lang}")
    except LangDetectException:
        print("=> Không phát hiện được ngôn ngữ, mặc định là tiếng Việt.")
        lang = 'vi'

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
    results = collection.query(query_texts=[user_query], n_results=7) # Lấy nhiều kết quả hơn để tăng ngữ cảnh

    context_data = None
    if results and results['documents'] and results['documents'][0]:
        context_data = "\n---\n".join(results['documents'][0])
        print("Tìm thấy ngữ cảnh, bắt đầu tạo prompt cho Gemini.")

    # 4. Tạo prompt và định nghĩa các kênh liên hệ
    # *** BẮT ĐẦU CẬP NHẬT LOGIC VÀ PROMPT ***
    if lang == 'en':
        system_prompt = """You are a smart and flexible virtual assistant for "HD Fitness and Yoga".

**TASK:**
Understand the main topic of the customer's question. Provide the most relevant and helpful information from the **REFERENCE TEXT**.

**PROCESSING RULES:**
1.  **Identify Main Topic:** Find the core topic of the question (e.g., in "advice for gym", the main topic is "gym"; in "yoga registration for 2 people", the topics are "yoga" and "group registration").
2.  **Provide Relevant Information:**
    * **Priority 1 (Direct Answer):** If the reference text contains a direct answer, answer the question straight to the point.
    * **Priority 2 (Provide Related Info):** If there is no direct answer, find and provide **ALL** information in the text related to the **main topic**. For example, if the user asks for "gym advice", provide information on gym prices, gym promotions, and PT services for the gym.
3.  **When No Information Exists:** Only if the reference text contains **absolutely no information** about the main topic, you must return the exact string: `NO_INFO_FOUND`.
4.  **Be Concise and Friendly:** Keep the answer brief, natural, and helpful.
5.  **Language:** Always answer in English.
"""
        contact_info_text = (
            "I'm sorry, I don't have information about that yet. "
            "For details, please contact my human colleagues through these channels:\n\n"
            "- Official Zalo: HD fitness and yoga, number 033244646\n"
            "- Technical Support: Zalo, number 0971166684\n"
            "- Emergency Hotline: 0979764885"
        )
    else:  # Mặc định là tiếng Việt
        system_prompt = """**Bối cảnh:** Bạn là một trợ lý ảo thông minh và linh hoạt của trung tâm "HD Fitness and Yoga".

**Nhiệm vụ:**
Hiểu rõ chủ đề chính trong câu hỏi của khách hàng. Cung cấp thông tin liên quan và hữu ích nhất từ **TÀI LIỆU THAM KHẢO**.

**QUY TẮC XỬ LÝ:**
1.  **Xác định Chủ Đề Chính:** Tìm chủ đề cốt lõi trong câu hỏi (ví dụ: trong "tư vấn gym", chủ đề chính là "gym"; trong "đăng ký yoga cho 2 người", chủ đề là "yoga" và "đăng ký nhóm").
2.  **Cung Cấp Thông Tin Liên Quan:**
    * **Ưu tiên 1 (Trả lời trực tiếp):** Nếu tài liệu có câu trả lời chính xác cho câu hỏi, hãy trả lời thẳng vào vấn đề.
    * **Ưu tiên 2 (Cung cấp thông tin liên quan):** Nếu không có câu trả lời trực tiếp, hãy tìm và cung cấp **TẤT CẢ** thông tin trong tài liệu có liên quan đến **chủ đề chính** của câu hỏi. Ví dụ, nếu khách hỏi "tư vấn gym", hãy cung cấp thông tin về giá gói tập gym, các chương trình khuyến mãi cho gym, và thông tin về PT cho gym.
3.  **Khi Không Có Thông Tin:** Chỉ khi tài liệu **hoàn toàn không chứa bất kỳ thông tin nào** về chủ đề chính của câu hỏi, bạn mới được trả về chuỗi ký tự `NO_INFO_FOUND`.
4.  **Ngắn Gọn và Thân Thiện:** Giữ câu trả lời súc tích, tự nhiên và hữu ích.
5.  **Ngôn Ngữ:** Luôn trả lời bằng tiếng Việt.
"""
        contact_info_text = (
            "Xin lỗi, tôi chưa có thông tin về vấn đề này. "
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

    **TÀI LIỆU THAM KHẢO:**
    {context_data}

    **Câu hỏi của khách hàng:**
    "{user_query}"

    **Câu trả lời của bạn:**
    """
    try:
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        print(f"=> Gemini đã trả lời: '{response_text}'")

        # Kiểm tra xem AI có trả về mã đặc biệt không
        if response_text == "NO_INFO_FOUND":
            print("=> Gemini không tìm thấy câu trả lời, hiển thị thông tin liên hệ.")
            return contact_info_text
        else:
            # Nếu có câu trả lời, trả về cho người dùng
            return response_text

    except Exception as e:
        print(f"Lỗi khi gọi Gemini API: {e}")
        # Nếu có lỗi xảy ra với API, cũng trả về thông tin liên hệ
        return contact_info_text
    # *** KẾT THÚC CẬP NHẬT LOGIC ***


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