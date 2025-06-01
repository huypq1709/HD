import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

chrome_options = Options()
# chrome_options.add_argument("--headless")  # Kích hoạt chế độ headless
chrome_options.add_argument("--disable-gpu") # Tắt GPU (đôi khi cần thiết cho headless trên Linux)
chrome_options.add_argument("--window-size=1920,1080") # Đặt kích thước cửa sổ ảo

driver = webdriver.Chrome(options=chrome_options)
driver.get("https://chat.zalo.me/")
time.sleep(100)
# ... sau đó thực hiện các thao tác tự động hóa