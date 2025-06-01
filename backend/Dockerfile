# File: backend/Dockerfile (PHIÊN BẢN SỬA LỖI CHROME)

# Bắt đầu từ image Python
FROM python:3.9-slim

# === BƯỚC 1: Cài đặt các gói cần thiết và Google Chrome ===
# Cập nhật và cài đặt các gói cơ bản
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
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
RUN wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && apt-get update \
    # dpkg -i có thể lỗi nếu thiếu dependencies, nhưng chúng ta đã cài ở trên
    # Dùng apt-get install -fy để tự sửa lỗi dependencies nếu có
    && dpkg -i google-chrome-stable_current_amd64.deb || apt-get install -fy \
    && rm google-chrome-stable_current_amd64.deb

# === BƯỚC 2: Cài đặt ChromeDriver tương thích ===
# Xác định phiên bản Chrome đã cài
RUN CHROME_MAJOR_VERSION=$(google-chrome --version | sed -E 's/.* ([0-9]+)\..*/\1/') \
    # Lấy phiên bản ChromeDriver mới nhất cho phiên bản Chrome đó
    && CHROME_DRIVER_VERSION=$(wget -qO- "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_MAJOR_VERSION}") \
    && echo "Installing ChromeDriver version: ${CHROME_DRIVER_VERSION}" \
    && wget -q "https://chromedriver.storage.googleapis.com/${CHROME_DRIVER_VERSION}/chromedriver_linux64.zip" \
    && unzip chromedriver_linux64.zip -d /usr/local/bin/ \
    && rm chromedriver_linux64.zip \
    && chmod +x /usr/local/bin/chromedriver

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