// Hàm phát âm thanh hướng dẫn theo số thứ tự và ngôn ngữ
export function playSound(soundId: number, language: string) {
  const lang = language === "en" ? "en" : "vi";
  const audio = new Audio(`/sounds/sound${soundId}_${lang}.mp3`);
  audio.play();
} 