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


# === BƯỚC 2: Cài đặt ChromeDriver tương thích (SỬA LẠI CÁCH GIẢI NÉN/DI CHUYỂN) ===
RUN CHROME_MAJOR_VERSION=$(google-chrome --product-version | cut -d. -f1) \
    && echo "Detected Chrome Major Version: $CHROME_MAJOR_VERSION" \
    && CHROME_DRIVER_VERSION=$(curl -sSL https://googlechromelabs.github.io/chrome-for-testing/LATEST_RELEASE_${CHROME_MAJOR_VERSION}) \
    && echo "Attempting to install ChromeDriver version: ${CHROME_DRIVER_VERSION} for Chrome ${CHROME_MAJOR_VERSION}" \
    && wget -q "https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/${CHROME_DRIVER_VERSION}/linux64/chromedriver-linux64.zip" -O chromedriver_linux64.zip \
    # Tạo thư mục tạm để giải nén, tránh ghi đè lung tung
    && mkdir /tmp/chromedriver_temp \
    && unzip chromedriver_linux64.zip -d /tmp/chromedriver_temp/ \
    # Di chuyển file thực thi chromedriver vào đúng vị trí
    && mv /tmp/chromedriver_temp/chromedriver-linux64/chromedriver /usr/local/bin/chromedriver \
    # Dọn dẹp
    && rm chromedriver_linux64.zip \
    && rm -rf /tmp/chromedriver_temp \
    && chmod +x /usr/local/bin/chromedriver \
    && echo "ChromeDriver installed. Version:" \
    && chromedriver --version

# === BƯỚC 3: Cài đặt các ứng dụng Python (như cũ) ===
RUN apt-get update && apt-get install -y supervisor --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt gunicorn

COPY . .
RUN python preload_models.py

COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# === BƯỚC 4: Khởi chạy (như cũ) ===
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]