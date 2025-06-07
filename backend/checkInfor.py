from flask import Flask, request, jsonify
from flask_cors import CORS
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service as ChromeService
from bs4 import BeautifulSoup
import time
import tempfile
import shutil
import threading
import uuid
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Lưu trữ trạng thái và kết quả của các task
task_status = {}
task_results = {}

def process_check_phone_task(task_id, phone_number):
    """Hàm xử lý việc kiểm tra thông tin trong background thread"""
    try:
        task_status[task_id] = "processing"
        
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")

        service = ChromeService(executable_path='/usr/local/bin/chromedriver')
        driver = None
        
        try:
            driver = webdriver.Chrome(service=service, options=chrome_options)
            driver.get("https://hdfitnessyoga.timesoft.vn/")

            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "UserName"))).send_keys("Vuongvv")
            WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.ID, "Password"))).send_keys("291199")
            WebDriverWait(driver, 3).until(EC.element_to_be_clickable((By.ID, "btnLogin"))).click()

            time.sleep(5)

            radio_all = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.ID, "radio_0"))
            )
            radio_all.click()
            time.sleep(0.5)

            search_input = WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input.form-control.form-search-main"))
            )
            search_input.clear()
            search_input.send_keys(phone_number)
            search_input.send_keys(Keys.ENTER)

            time.sleep(0.5)

            html_content = driver.page_source
            soup = BeautifulSoup(html_content, "html.parser")

            table_body = soup.find("tbody", class_="show-table-ready")
            rows = table_body.find_all("tr") if table_body else []

            data_list = []

            for row in rows:
                cols = row.find_all("td")
                if len(cols) < 7:
                    continue

                name_elem = cols[0].find("span", class_="ng-binding")
                name = name_elem.text.strip() if name_elem else ""
                phone_text = cols[2].text.strip()
                service_text = cols[3].text.strip()
                
                remaining = ""
                span_list = cols[5].find_all("span")
                if span_list:
                    remaining = span_list[0].text.strip()

                start_date = cols[6].text.strip()
                end_date = cols[7].text.strip()

                status_span = row.find("span", class_=lambda value: value and "status-" in value)
                status = status_span.text.strip() if status_span else ""

                data_list.append({
                    "name": name,
                    "phone": phone_text,
                    "service": service_text,
                    "remaining": remaining,
                    "start_date": start_date,
                    "end_date": end_date,
                    "status": status
                })

            task_results[task_id] = {"results": data_list}
            task_status[task_id] = "completed"
            
        except Exception as e:
            error_message = f"Error in check_phone: {type(e).__name__} - {str(e)}"
            task_results[task_id] = {"error": error_message}
            task_status[task_id] = "error"
            
        finally:
            if driver:
                driver.quit()
                
    except Exception as e:
        task_results[task_id] = {"error": str(e)}
        task_status[task_id] = "error"

@app.route("/check-phone", methods=["POST"])
def check_phone():
    data = request.get_json()
    phone_number = data.get("phone", "")
    
    if not phone_number or len(phone_number) != 10 or not phone_number.isdigit():
        return jsonify({"error": "Invalid phone number"}), 400

    # Tạo task_id mới
    task_id = str(uuid.uuid4())
    task_status[task_id] = "pending"
    task_results[task_id] = None

    # Khởi chạy task trong background thread
    thread = threading.Thread(target=process_check_phone_task, args=(task_id, phone_number))
    thread.daemon = True
    thread.start()

    # Trả về task_id ngay lập tức
    return jsonify({
        "task_id": task_id,
        "status": "pending",
        "message": "Task started successfully"
    })

@app.route("/check-task-status/<task_id>", methods=["GET"])
def check_task_status(task_id):
    """API endpoint để kiểm tra trạng thái của task"""
    if task_id not in task_status:
        return jsonify({"error": "Task not found"}), 404

    status = task_status[task_id]
    response = {
        "task_id": task_id,
        "status": status
    }

    if status == "completed":
        response["data"] = task_results[task_id]
        # Xóa task đã hoàn thành sau 5 phút
        threading.Timer(300, lambda: cleanup_task(task_id)).start()
    elif status == "error":
        response["error"] = task_results[task_id].get("error", "Unknown error")
        # Xóa task lỗi sau 5 phút
        threading.Timer(300, lambda: cleanup_task(task_id)).start()

    return jsonify(response)

def cleanup_task(task_id):
    """Xóa task và kết quả của nó khỏi bộ nhớ"""
    if task_id in task_status:
        del task_status[task_id]
    if task_id in task_results:
        del task_results[task_id]

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

