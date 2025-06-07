import { useEffect, useState } from "react";
import { ChevronLeftIcon, ChevronRightIcon } from "lucide-react";

interface IntroScreenProps {
  onRegister: (action: string) => void;
  language: string;
}

export function IntroScreen({ onRegister, language }: IntroScreenProps) {
  const [currentSlide, setCurrentSlide] = useState(0);
  const slides = [
    { url: "/discount.jpg", alt: "Summer 2025" },
    { url: "/price.jpg", alt: "Price" },
    { url: "/gym_5.jpg", alt: "Modern gym reception area" },
    { url: "/gym6.jpg", alt: "Weight training area" },
    { url: "/gym4.jpg", alt: "Cardio equipment area" },
    { url: "/gym3.jpg", alt: "Functional training area" },
    { url: "/gym2.jpg", alt: "Additional training area" }
  ];

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentSlide((prev) => (prev + 1) % slides.length);
    }, 10000);
    return () => clearInterval(timer);
  }, [slides.length]);

  const nextSlide = () => {
    setCurrentSlide((prev) => (prev + 1) % slides.length);
  };
  const prevSlide = () => {
    setCurrentSlide((prev) => (prev - 1 + slides.length) % slides.length);
  };

  return (
      <div className="space-y-8">
        <div className="relative h-96 overflow-hidden rounded-xl">
          <div className="relative h-full">
            {slides.map((slide, index) => (
                <div
                    key={index}
                    className={`absolute w-full h-full transition-opacity duration-500 ${
                        currentSlide === index ? "opacity-100" : "opacity-0"
                    }`}
                >
                  <img src={slide.url} alt={slide.alt} className="w-full h-full object-cover" />
                </div>
            ))}
          </div>
          <button
              onClick={prevSlide}
              aria-label={language === "en" ? "Previous slide" : "Trang trước"}
              title={language === "en" ? "Previous slide" : "Trang trước"}
              className="absolute left-4 top-1/2 -translate-y-1/2 p-2 rounded-full bg-white/80 hover:bg-white text-gray-800"
          >
            <span style={{position: 'absolute', width: 1, height: 1, padding: 0, margin: -1, overflow: 'hidden', clip: 'rect(0,0,0,0)', border: 0}}>
              {language === "en" ? "Previous slide" : "Trang trước"}
            </span>
            <ChevronLeftIcon className="h-6 w-6" />
          </button>
          <button
              onClick={nextSlide}
              aria-label={language === "en" ? "Next slide" : "Trang sau"}
              title={language === "en" ? "Next slide" : "Trang sau"}
              className="absolute right-4 top-1/2 -translate-y-1/2 p-2 rounded-full bg-white/80 hover:bg-white text-gray-800"
          >
            <span style={{position: 'absolute', width: 1, height: 1, padding: 0, margin: -1, overflow: 'hidden', clip: 'rect(0,0,0,0)', border: 0}}>
              {language === "en" ? "Next slide" : "Trang sau"}
            </span>
            <ChevronRightIcon className="h-6 w-6" />
          </button>
          <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2 flex space-x-2">
            {slides.map((_, index) => (
                <button
                    key={index}
                    onClick={() => setCurrentSlide(index)}
                    className={`w-2 h-2 rounded-full transition-all ${
                        currentSlide === index ? "bg-white w-4" : "bg-white/50"
                    }`}
                />
            ))}
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4"> {/* Thay đổi grid-cols-3 thành grid-cols-4 */}
          <button
              onClick={() => onRegister("register")}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors"
          >
            {language === "en" ? "Register/Renew" : "Đăng Ký/ Gia Hạn "}
          </button>
          <button
              onClick={() => onRegister("check")}
              className="px-6 py-3 bg-gray-100 text-gray-700 rounded-lg font-medium hover:bg-gray-200 transition-colors"
          >
            {language === "en" ? "Check Information" : "Kiểm Tra Thông Tin"}
          </button>
          <button
              onClick={() => onRegister("guide")}
              className="px-6 py-3 bg-black text-white rounded-lg font-medium hover:bg-gray-900 transition-colors"
          >
            {language === "en" ? "Guide" : "Hướng dẫn"}
          </button>
          <button
              onClick={() => onRegister("faceid")}
              className="px-6 py-3 bg-red-600 text-white rounded-lg font-medium hover:bg-red-700 transition-colors"
          >
            {language === "en" ? "Update Face ID" : "Cập Nhật Face ID "}
          </button>
        </div>
      </div>


  );
}