# # File: backend/checkInfor.py (Thêm các dòng PRINT DEBUG)
# print("DEBUG: checkInfor.py - Bắt đầu import các module") # PRINT 1
#
# from flask import Flask, request, jsonify
# from flask_cors import CORS
# # Di chuyển các import của Selenium và BeautifulSoup ra ngoài hàm nếu chúng chỉ dùng trong hàm này
# # Hoặc để ở đầu file nếu dùng ở nhiều nơi khác trong file checkInfor.py
# print("DEBUG: checkInfor.py - Chuẩn bị import Selenium và BS4") # PRINT 1.1
# from selenium import webdriver
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.webdriver.common.keys import Keys
# from selenium.webdriver.chrome.service import Service as ChromeService  # Nên dùng
# from bs4 import BeautifulSoup
# import time
# import tempfile  # Thêm import này cho giải pháp thư mục tạm
# import shutil  # Thêm import này để xóa thư mục tạm
# print("DEBUG: checkInfor.py - Đã import xong Selenium và BS4") # PRINT 1.2
#
#
# print("DEBUG: checkInfor.py - Chuẩn bị khởi tạo Flask app") # PRINT 2
# app = Flask(__name__)
# CORS(app)
# print("DEBUG: checkInfor.py - Đã khởi tạo Flask app và CORS") # PRINT 3
#
#
# @app.route("/check-phone", methods=["POST"])
# def check_phone():
#     print("DEBUG: checkInfor.py - Nhận được yêu cầu vào /check-phone") # PRINT A
#     data = request.get_json()
#     phone_number = data.get("phone", "")
#     if not phone_number or len(phone_number) != 10 or not phone_number.isdigit():
#         print(f"DEBUG: checkInfor.py - Số điện thoại không hợp lệ: {phone_number}") # PRINT B1
#         return jsonify({"error": "Invalid phone number"}), 400
#
#     print(f"DEBUG: checkInfor.py - Bắt đầu xử lý cho số điện thoại: {phone_number}") # PRINT B2
#
#     chrome_options = Options()
#     chrome_options.add_argument("--headless=new")
#     chrome_options.add_argument("--no-sandbox")
#     chrome_options.add_argument("--disable-dev-shm-usage")
#     chrome_options.add_argument("--disable-gpu")
#     chrome_options.add_argument("--window-size=1920,1080")
#
#     print("DEBUG: checkInfor.py - Đã cấu hình chrome_options") # PRINT C
#
#     # service = ChromeService() # Nếu chromedriver đã trong PATH và tương thích
#     # Hoặc chỉ định rõ đường dẫn nếu cần:
#     service = ChromeService(executable_path='/usr/local/bin/chromedriver')
#     print("DEBUG: checkInfor.py - Đã cấu hình ChromeService") # PRINT D
#
#     driver = None
#     try:
#         print("DEBUG: checkInfor.py - Chuẩn bị khởi tạo WebDriver") # PRINT E
#         driver = webdriver.Chrome(service=service, options=chrome_options)
#         print("DEBUG: checkInfor.py - WebDriver đã được khởi tạo") # PRINT F
#
#         print("DEBUG: checkInfor.py - Chuẩn bị driver.get('https://hdfitnessyoga.timesoft.vn/')") # PRINT G
#         driver.get("https://hdfitnessyoga.timesoft.vn/")
#         print("DEBUG: checkInfor.py - driver.get() hoàn thành") # PRINT H
#
#         # ... (phần còn lại của code Selenium của bạn, bạn có thể thêm print vào đây nữa) ...
#
#         WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "UserName"))).send_keys(
#             "Vuongvv")
#         print("DEBUG: checkInfor.py - Đã nhập UserName") # PRINT I
#         # ... (Thêm print sau mỗi bước quan trọng của Selenium)
#
#         # ... (phần còn lại của code) ...
#
#         return jsonify({"results": "SOME_DATA_HERE"}) # Thay thế bằng dữ liệu thật
#
#     except Exception as e:
#         error_message = f"Error in check_phone: {type(e).__name__} - {str(e)}"
#         print(f"DEBUG: checkInfor.py - GẶP LỖI: {error_message}") # PRINT ERROR
#         return jsonify({"error": error_message}), 500
#     finally:
#         print("DEBUG: checkInfor.py - Vào khối finally") # PRINT FINALLY
#         if driver:
#             driver.quit()
#             print("DEBUG: checkInfor.py - Đã gọi driver.quit()") # PRINT QUIT
#         # ... (phần xử lý temp_user_data_dir nếu có) ...
#
#
# # Dòng này chỉ để chạy test trực tiếp file Python, không ảnh hưởng khi chạy với Gunicorn
# if __name__ == "__main__":
#     print("DEBUG: checkInfor.py - Chạy ở chế độ __main__ (test cục bộ)") # PRINT MAIN
#     app.run(host="0.0.0.0", port=5000, debug=True) # Đã sửa lại cổng cho khớp
# File: backend/checkInfor.py (PHIÊN BẢN SIÊU ĐƠN GIẢN ĐỂ TEST LẠI)
print("DEBUG_SIMPLE_CI: checkInfor.py - SCRIPT STARTED!")

from flask import Flask
app = Flask(__name__)

@app.route('/check-phone', methods=['POST'])
def simplified_check_phone_route():
    print("DEBUG_SIMPLE_CI: checkInfor.py - /check-phone POST route called")
    return "Hello from SIMPLIFIED checkInfor.py /check-phone POST!"

@app.route('/') # Thêm một route GET đơn giản
def simplified_root_route():
    print("DEBUG_SIMPLE_CI: checkInfor.py - / (GET) route called")
    return "Hello from SIMPLIFIED checkInfor.py root GET!"

print("DEBUG_SIMPLE_CI: checkInfor.py - SCRIPT LOADED, FLASK APP CREATED.")