import React, { useEffect } from "react";
import { DumbbellIcon } from "lucide-react";
import { Slogan } from "./Slogan";
import { playSound, stopSound } from "../utils/playSound";

interface ServiceScreenProps {
    formData: any;
    updateFormData: (field: string, value: any) => void;
    nextStep: () => void;
    prevStep: () => void;
    language: string;
}

export function ServiceScreen(props: ServiceScreenProps) {
    const { formData, updateFormData, nextStep, prevStep, language } = props;

    const handleSelect = (service: string) => {
        updateFormData("service", service);
        nextStep();
    };

    useEffect(() => {
        console.log('Play sound ServiceScreen', language);
        stopSound();
        playSound(4, language);
        return () => { stopSound(); };
    }, [language]);

    return (
        <div className="space-y-6">
            <h2 className="text-xl font-semibold text-gray-800">
                {language === "en" ? "Select a Service" : "Chọn Dịch Vụ"}
            </h2>
            <p className="text-gray-600">
                {language === "en" ? "What service are you interested in?" : "Bạn quan tâm đến dịch vụ nào?"}
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Gym Button */}
                <button
                    onClick={() => handleSelect("gym")}
                    className={`p-6 border rounded-lg flex flex-col items-center transition-all hover:bg-blue-50 ${
                        formData.service === "Gym" ? "border-blue-500 bg-blue-50" : "border-gray-200"
                    }`}
                >
                    <DumbbellIcon className="h-12 w-12 mb-2 text-blue-500" />
                    <span className="font-medium text-gray-800">
            {language === "en" ? "Gym" : "GYM"}
          </span>
                    <p className="text-sm text-gray-500 mt-2 text-center">
                        {language === "en"
                            ? "Full access to gym equipment and facilities"
                            : "Sử dụng đầy đủ thiết bị và tiện ích phòng tập gym"}
                    </p>
                </button>

                {/* Yoga Button with icon */}
                <button
                    onClick={() => handleSelect("yoga")}
                    className={`p-6 border rounded-lg flex flex-col items-center transition-all hover:bg-blue-50 ${
                        formData.service === "Yoga" ? "border-blue-500 bg-blue-50" : "border-gray-200"
                    }`}
                >
                    {/* Image icon for Yoga */}
                    <img
                        src="/yoga.png" // Đảm bảo rằng bạn đã tải icon yoga vào thư mục public/images/
                        alt="Yoga"
                        className="h-12 w-12 mb-2"
                    />
                    <span className="font-medium text-gray-800">Yoga</span>
                    <p className="text-sm text-gray-500 mt-2 text-center">
                        {language === "en" ? (
                            <>
                                Take a Yoga class with an instructor
                                <br /> {/* Xuống dòng */}
                                **Schedule:**
                                <br />
                                Monday, Wednesday, Friday: 6:30 PM - 7:30 PM


                            </>
                        ) : (
                            <>
                                Tham gia lớp Yoga có giáo viên hướng dẫn
                                <br /> {/* Xuống dòng */}
                                **Lịch tập:**
                                <br />
                                Thứ Hai, Thứ Tư, Thứ Sáu: 18:30 - 19:30

                            </>
                        )}
                    </p>
                </button>
            </div>
            <div className="flex justify-between pt-4">
                <button
                    onClick={prevStep}
                    className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                    {language === "en" ? "Back" : "Quay lại"}
                </button>
            </div>
            <Slogan
                message={
                    language === "en"
                        ? "Please re-rack your weights after use and keep the equipment organized."
                        : "Vui lòng xếp tạ về vị trí sau khi sử dụng và giữ thiết bị ngăn nắp."
                }
                language={language}
            />
        </div>
    );
}
