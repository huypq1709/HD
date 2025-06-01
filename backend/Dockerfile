# File: backend/Dockerfile (PHIÊN BẢN SỬA LỖI CHROME - Lần 2)

FROM python:3.9-slim

# === BƯỚC 1: Cài đặt các gói cần thiết và Google Chrome ===
# Cập nhật và cài đặt các gói cơ bản
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    # Các thư viện phụ thuộc thường cần cho Chrome
    libglib2.0-0 \
    libnss3 \
    libgconf-2-4 \
    libfontconfig1 \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libc6 \
    libcairo2 \
    libcups2 \
    libdbus-1-3 \
    libexpat1 \
    libgcc1 \
    libgbm1 \
    libgdk-pixbuf2.0-0 \
    libgtk-3-0 \
    libnspr4 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libstdc++6 \
    libx11-6 \
    libx11-xcb1 \
    libxcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxi6 \
    libxrandr2 \
    libxrender1 \
    libxss1 \
    libxtst6 \
    ca-certificates \
    lsb-release \
    xdg-utils \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Thêm Google Chrome repository và cài đặt Chrome
# Đảm bảo rằng khóa được thêm đúng cách và source list được tạo chính xác
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-chrome-keyring.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome-keyring.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# === BƯỚC 2: Cài đặt ChromeDriver tương thích ===
# Kiểm tra xem google-chrome có thực sự chạy được không
RUN google-chrome --version || echo "google-chrome command failed but continuing"

# Cố gắng lấy CHROME_VERSION một cách an toàn hơn
RUN CHROME_VERSION_FULL=$(google-chrome --version 2>/dev/null || echo "unknown") \
    && if [ "$CHROME_VERSION_FULL" != "unknown" ]; then \
         CHROME_MAJOR_VERSION=$(echo "$CHROME_VERSION_FULL" | sed -E 's/.* ([0-9]+)\..*/\1/'); \
       else \
         echo "Failed to get Chrome version, defaulting to a common recent version for ChromeDriver"; \
         CHROME_MAJOR_VERSION="120"; \
       fi \
    # Tiếp tục với CHROME_MAJOR_VERSION đã xác định (hoặc mặc định)
    && CHROME_DRIVER_VERSION=$(wget -qO- "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_MAJOR_VERSION}") \
    # Nếu không tìm thấy LATEST_RELEASE, thử với phiên bản cụ thể hơn
    && if [ -z "$CHROME_DRIVER_VERSION" ]; then CHROME_DRIVER_VERSION=$(wget -qO- "https://googlechromelabs.github.io/chrome-for-testing/LATEST_RELEASE_${CHROME_MAJOR_VERSION}"); fi \
    && if [ -z "$CHROME_DRIVER_VERSION" ]; then echo "Still cannot find ChromeDriver version for Chrome ${CHROME_MAJOR_VERSION}, trying fixed version"; CHROME_DRIVER_VERSION="120.0.6099.109"; fi \
    && echo "Attempting to install ChromeDriver version: ${CHROME_DRIVER_VERSION}" \
    # Thử tải từ endpoint mới của Chrome for Testing nếu có
    && wget -q "https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/${CHROME_DRIVER_VERSION}/linux64/chromedriver-linux64.zip" -O chromedriver_linux64.zip \
    || wget -q "https://chromedriver.storage.googleapis.com/${CHROME_DRIVER_VERSION}/chromedriver_linux64.zip" -O chromedriver_linux64.zip \
    && unzip chromedriver_linux64.zip -d /usr/local/bin/ \
    && rm chromedriver_linux64.zip \
    && chmod +x /usr/local/bin/chromedriver \
    && chromedriver --version


# === BƯỚC 3: Cài đặt các ứng dụng Python (như cũ) ===
RUN apt-get update && apt-get install -y supervisor --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt gunicorn

COPY . .

COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# === BƯỚC 4: Khởi chạy (như cũ) ===
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]