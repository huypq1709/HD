# test_new.py

# Import trực tiếp các hàm từ auto_dk.py
from auto_dk import _initialize_driver, _login_to_timesoft, _automate_for_new_customer_sync

import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

# Đổi tên hàm để Pytest nhận diện là một test
def test_new_customer_registration(): # Đã đổi tên hàm ở đây!
    """
    Hàm để chạy thử nghiệm tự động hóa đăng ký khách hàng mới một cách độc lập.
    """
    # --- CẤU HÌNH THÔNG TIN TEST CHO KHÁCH HÀNG MỚI ---
    # CHÚ Ý: Số điện thoại này KHÔNG NÊN tồn tại trong hệ thống Timesoft của bạn
    # để đảm bảo kịch bản "khách hàng mới" là đúng.
    TEST_PHONE_NUMBER = "0901234567" # Thay bằng SĐT ĐỘC NHẤT (chưa có trong Timesoft)
    TEST_FULL_NAME = "Nguyễn Văn Test Mới" # Tên đầy đủ của khách hàng mới
    TEST_SERVICE_TYPE = "Yoga"          # Phải khớp với key trong NEW_CUSTOMER_PACKAGES_MAP (ví dụ: "Yoga", "GYM", "Zumba")
    TEST_MEMBERSHIP_TYPE = "1year" # Phải khớp với key gói tập cụ thể trong NEW_CUSTOMER_PACKAGES_MAP[TEST_SERVICE_TYPE]

    print(f"\n--- Bắt đầu Test Tự động hóa Đăng ký Khách hàng Mới ---")
    print(f"Số điện thoại: {TEST_PHONE_NUMBER}")
    print(f"Họ và tên: {TEST_FULL_NAME}")
    print(f"Loại dịch vụ: {TEST_SERVICE_TYPE}")
    print(f"Gói tập: {TEST_MEMBERSHIP_TYPE}")

    # Kiểm tra xem gói tập có tồn tại trong ánh xạ không

    result = _automate_for_new_customer_sync(TEST_PHONE_NUMBER, TEST_FULL_NAME, TEST_SERVICE_TYPE, TEST_MEMBERSHIP_TYPE)

    if result["status"] == "success":
        print(f"🎉 Test thành công: {result['message']}")
        assert True # Đánh dấu test là thành công
    else:
        print(f"❌ Test thất bại: {result['message']}")
        assert False, result["message"] # Đánh dấu test là thất bại và hiển thị thông báo lỗi

    print(f"--- Kết thúc Test Tự động hóa Đăng ký Khách hàng Mới ---")

# Loại bỏ khối `if __name__ == "__main__":` vì Pytest sẽ tự động tìm và chạy hàm `test_*`
# Bạn không cần gọi hàm test thủ công khi sử dụng Pytest.