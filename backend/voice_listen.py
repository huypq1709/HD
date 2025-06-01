import sounddevice as sd
import numpy as np
import time

def test_speaker_volume(duration=5, sample_rate=44100, channels=1):
    """
    Ghi âm trong một khoảng thời gian và in ra độ lớn âm thanh lớn nhất phát hiện được.

    Args:
        duration (int): Thời gian ghi âm (giây).
        sample_rate (int): Tần số lấy mẫu âm thanh (Hz).
        channels (int): Số kênh âm thanh.
    """
    max_volume = 0

    def audio_callback(indata, frames, time, status):
        nonlocal max_volume
        if status:
            print(f"Lỗi audio: {status}")
            return
        volume_norm = np.linalg.norm(indata) * 10  # Tính độ lớn
        max_volume = max(max_volume, volume_norm)

    try:
        print(f"🔊 Bắt đầu ghi âm để test loa trong {duration} giây...")
        with sd.InputStream(samplerate=sample_rate, channels=channels, callback=audio_callback):
            time.sleep(duration)
        print(f"🔊 Kết thúc ghi âm.")
        print(f"🔊 Độ lớn âm thanh lớn nhất phát hiện được: {max_volume:.4f}")

    except Exception as e:
        print(f"❌ Lỗi khi test loa: {e}")

if __name__ == '__main__':
    test_speaker_volume(duration=20) # Test trong 10 giây
    print("\n Hãy thử phát âm thanh từ loa của bạn trong khi script đang chạy.")
    test_speaker_volume(duration=20) # Test lần nữa để bạn phát âm thanh