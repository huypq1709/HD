import { useState, FormEvent, useEffect } from "react";
import { Slogan } from "./Slogan";
import { playSound, stopSound } from "../utils/playSound";

// Định nghĩa kiểu dữ liệu cho props
interface NameScreenProps {
  formData: {
    fullName: string;
    [key: string]: any; // cho phép có thêm thuộc tính khác nếu cần
  };
  updateFormData: (field: string, value: string) => void;
  nextStep: () => void;
  prevStep: () => void;
  language: string;
  resetToIntro: () => void;
}

export function NameScreen({
                             formData,
                             updateFormData,
                             nextStep,
                             prevStep,
                             language,
                             resetToIntro
                           }: NameScreenProps) {
  const [error, setError] = useState("");

  // Khai báo kiểu cho event là FormEvent<HTMLFormElement>
  const handleSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!formData.fullName.trim()) {
      setError(language === "en" ? "Please enter your full name" : "Vui lòng nhập họ và tên của bạn");
      return;
    }
    nextStep();
  };

  useEffect(() => {
    stopSound();
    playSound(2, language);
    return () => { stopSound(); };
  }, [language]);

  // useEffect: Nếu có lỗi hiển thị lên màn hình thì sau 60 giây sẽ reload lại và trở về Intro
  useEffect(() => {
    if (typeof error === 'string' && error && (
      error.toLowerCase().includes("lỗi") ||
      error.toLowerCase().includes("thất bại") ||
      error.toLowerCase().includes("error") ||
      error.toLowerCase().includes("failed")
    )) {
      const timer = setTimeout(() => {
        window.location.reload();
        if (typeof resetToIntro === 'function') resetToIntro();
      }, 60000);
      return () => clearTimeout(timer);
    }
  }, [error, resetToIntro]);

  return (
      <div className="space-y-6">
        <h2 className="text-xl font-semibold text-gray-800">
          {language === "en" ? "Your Name" : "Tên của bạn"}
        </h2>
        <p className="text-gray-600">
          {language === "en" ? "Please enter your full name" : "Vui lòng nhập họ và tên của bạn"}
        </p>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label
                htmlFor="fullName"
                className="block text-sm font-medium text-gray-700 mb-1"
            >
              {language === "en" ? "Full Name" : "Họ và Tên"}
            </label>
            <input
                type="text"
                id="fullName"
                value={formData.fullName}
                onChange={(e) => {
                  updateFormData("fullName", e.target.value);
                  setError("");
                }}
                className={`w-full p-2 border rounded-md focus:ring-2 focus:ring-blue-500 focus:outline-none ${
                    error ? "border-red-500" : "border-gray-300"
                }`}
                placeholder={language === "en" ? "John Doe" : "Nguyễn Văn A"}
            />
            {error && <p className="mt-1 text-sm text-red-600">{error}</p>}
          </div>
          <div className="flex justify-between pt-4">
            <button
                type="button"
                onClick={prevStep}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {language === "en" ? "Back" : "Quay lại"}
            </button>
            <button
                type="submit"
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {language === "en" ? "Next" : "Tiếp tục"}
            </button>
          </div>
        </form>
        <Slogan
            message={
              language === "en"
                  ? "Respect others and maintain a friendly atmosphere in the gym."
                  : "Hãy giúp chúng tôi duy trì một không gian thân thiện và chào đón cho tất cả mọi người."
            }
            language={language}
        />
      </div>
  );
}
