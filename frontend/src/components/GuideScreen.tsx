// src/components/GuideScreen.tsx
import  { useState, useEffect } from "react";
import { ChevronLeftIcon, ChevronRightIcon } from "lucide-react";

interface GuideScreenProps {
    resetToIntro: () => void;
    language: string;
}

export function GuideScreen({ resetToIntro, language }: GuideScreenProps) {
    const slides = [
        { url: "/guide1.jpg", alt: language === "en" ? "Guide 1" : "Hướng dẫn 1" },
        { url: "/guide2.jpg", alt: language === "en" ? "Guide 2" : "Hướng dẫn 2" },
        { url: "/guide3.jpg", alt: language === "en" ? "Guide 3" : "Hướng dẫn 3" },
        { url: "/guide4.jpg", alt: language === "en" ? "Guide 4" : "Hướng dẫn 4" },
        { url: "/guide5.jpg", alt: language === "en" ? "Guide 5" : "Hướng dẫn 5" },
    ];

    const [currentSlide, setCurrentSlide] = useState(0);
    // Khởi tạo đếm ngược 5 phút (300 giây)
    const [autoReturnCountdown, setAutoReturnCountdown] = useState(150);

    useEffect(() => {
        // Auto slide: mỗi 5 giây chuyển sang slide kế tiếp
        const slideTimer = setInterval(() => {
            setCurrentSlide((prev) => (prev + 1) % slides.length);
        }, 30000);
        return () => clearInterval(slideTimer);
    }, [slides.length]);

    useEffect(() => {
        // Cập nhật countdown mỗi giây
        const intervalId = setInterval(() => {
            setAutoReturnCountdown((prev) => {
                if (prev <= 1) {
                    clearInterval(intervalId);
                    resetToIntro();
                    return 0;
                }
                return prev - 1;
            });
        }, 1000);
        return () => clearInterval(intervalId);
    }, [resetToIntro]);

    const nextSlide = () => {
        setCurrentSlide((prev) => (prev + 1) % slides.length);
    };

    const prevSlide = () => {
        setCurrentSlide((prev) => (prev - 1 + slides.length) % slides.length);
    };

    return (
        <div className="space-y-0 p-4">
            <h2 className="text-2xl font-semibold text-gray-800 text-center">
                {language === "en" ? "Guide for New Customers" : "Hướng Dẫn Cho Khách Hàng Mới"}
            </h2>
            <div className="relative h-96 overflow-hidden rounded-xl">
                <div className="relative h-full">
                    {slides.map((slide, index) => (
                        <div
                            key={index}
                            className={`absolute w-full h-full transition-opacity duration-500 ${
                                currentSlide === index ? "opacity-100" : "opacity-0"
                            }`}
                        >
                            <img src={slide.url} alt={slide.alt} className="w-full h-full object-contain" />
                        </div>
                    ))}
                </div>
                <button
                    onClick={prevSlide}
                    className="absolute left-4 top-1/2 -translate-y-1/2 p-2 bg-white/80 rounded-full hover:bg-white text-gray-800"
                >
                    <ChevronLeftIcon className="h-6 w-6" />
                </button>
                <button
                    onClick={nextSlide}
                    className="absolute right-4 top-1/2 -translate-y-1/2 p-2 bg-white/80 rounded-full hover:bg-white text-gray-800"
                >
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
            {/* Hiển thị countdown */}
            <p className=" text-gray-500 text-center">
                {language === "en"
                    ? `Auto return to Home in ${autoReturnCountdown} second${autoReturnCountdown === 1 ? "" : "s"}.`
                    : `Tự động trở về Trang Chủ sau ${autoReturnCountdown} giây.`}
            </p>
            <div className="flex justify-center">
                <button
                    onClick={resetToIntro}
                    className="px-4 py-2 bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
                >
                    {language === "en" ? "Back to Home" : "Quay lại Trang Chủ"}
                </button>
            </div>
        </div>
    );
}

export default GuideScreen;
