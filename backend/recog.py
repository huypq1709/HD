import speech_recognition as sr
import time

# Thời gian thu âm (2 phút = 120 giây)
thoi_gian_thu_am = 120

# Tạo một đối tượng Recognizer
r = sr.Recognizer()

# Sử dụng microphone làm nguồn âm thanh
with sr.Microphone() as source:
    print(f"Bắt đầu thu âm trong {thoi_gian_thu_am} giây...")
    r.adjust_for_ambient_noise(source)
    audio = r.listen(source, phrase_time_limit=thoi_gian_thu_am)
    print("Đã kết thúc thu âm.")

# Nhận diện giọng nói bằng Google Speech Recognition
try:
    print("Đang nhận diện...")
    text = r.recognize_google(audio, language='vi-VN')
    print(f"Đoạn âm thanh bạn đã nói: {text}")

    # Kiểm tra xem cụm từ "bạn đã nhận được" có trong đoạn văn bản đã nhận diện hay không
    if "bạn đã nhận được" in text.lower():
        print("Cụm từ 'bạn đã nhận được' đã được nhận diện.")
    else:
        print("Cụm từ 'bạn đã nhận được' không được nhận diện.")

except sr.UnknownValueError:
    print("Không thể nhận diện giọng nói trong đoạn âm thanh.")
except sr.RequestError as e:
    print(f"Lỗi dịch vụ nhận diện giọng nói; {e}")