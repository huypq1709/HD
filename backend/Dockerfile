# File: backend/Dockerfile (PHIÊN BẢN SỬA LỖI CHROME - Lần 3)

FROM python:3.9-slim

# === BƯỚC 1: Cài đặt các gói cần thiết và Google Chrome (Giữ nguyên như lần sửa trước) ===
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
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

RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-chrome-keyring.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome-keyring.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# === BƯỚC 2: Cài đặt một phiên bản ChromeDriver cụ thể (ĐƠN GIẢN HÓA) ===
# Chúng ta sẽ cài một phiên bản ChromeDriver khá phổ biến, ví dụ 114.0.5735.90
# Nếu sau này Selenium báo lỗi không tương thích, chúng ta sẽ điều chỉnh phiên bản này.
RUN CHROME_DRIVER_FIXED_VERSION="114.0.5735.90" \
    && echo "Attempting to install fixed ChromeDriver version: ${CHROME_DRIVER_FIXED_VERSION}" \
    && wget -q "https://chromedriver.storage.googleapis.com/${CHROME_DRIVER_FIXED_VERSION}/chromedriver_linux64.zip" -O chromedriver_linux64.zip \
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