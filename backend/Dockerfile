# File: backend/Dockerfile (PHIÊN BẢN MỚI)

# Bắt đầu từ image Python
FROM python:3.9-slim

# === BƯỚC 1: Cài đặt các gói cần thiết và Google Chrome ===
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    # Các thư viện phụ thuộc của Chrome
    libglib2.0-0 \
    libnss3 \
    libgconf-2-4 \
    libfontconfig1 \
    --no-install-recommends

# Tải và cài đặt Google Chrome
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list' \
    && apt-get update \
    && apt-get install -y google-chrome-stable

# === BƯỚC 2: Cài đặt ChromeDriver tương thích ===
# Tìm phiên bản Chrome đã cài và tải ChromeDriver phù hợp
RUN CHROME_VERSION=$(google-chrome --version | cut -f 3 -d ' ' | cut -d '.' -f 1) \
    && CHROME_DRIVER_VERSION=$(wget -qO- https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_VERSION}) \
    && wget -q https://chromedriver.storage.googleapis.com/${CHROME_DRIVER_VERSION}/chromedriver_linux64.zip \
    && unzip chromedriver_linux64.zip -d /usr/local/bin/ \
    && rm chromedriver_linux64.zip \
    && chmod +x /usr/local/bin/chromedriver

# === BƯỚC 3: Cài đặt các ứng dụng Python (như cũ) ===
# Cài đặt supervisor
RUN apt-get install -y supervisor

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt gunicorn

COPY . .

COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# === BƯỚC 4: Khởi chạy (như cũ) ===
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]