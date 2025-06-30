// Hàm phát âm thanh hướng dẫn theo số thứ tự và ngôn ngữ
let currentAudio: HTMLAudioElement | null = null;

export function playSound(soundId: number, language: string): HTMLAudioElement {
  if (currentAudio) {
    currentAudio.pause();
    currentAudio.currentTime = 0;
  }
  const lang = language === "en" ? "en" : "vi";
  const audio = new Audio(`/sounds/sound${soundId}_${lang}.mp3`);
  currentAudio = audio;
  audio.play();
  return audio;
}

export function stopSound() {
  if (currentAudio) {
    currentAudio.pause();
    currentAudio.currentTime = 0;
    currentAudio = null;
  }
} 