import React from "react";
import { Fingerprint } from "lucide-react";
import { Slogan } from "./Slogan";

export function AddFinger({ formData, language }){
    const title = language === "vi" ? "Thêm Vân Tay" : "Add Fingerprint";
    const instruction =
        language === "vi"
            ? "Xem video hướng dẫn dưới đây để biết cách lấy vân tay của bạn một cách chính xác."
            : "Watch the tutorial video below to learn how to capture your fingerprint accurately.";
    const captureButtonText = language === "vi" ? "Lấy vân tay" : "Capture Fingerprint";
    const sloganMessage =
        language === "vi"
            ? "Vân tay của bạn giúp bảo mật thông tin cá nhân."
            : "Your fingerprint enhances your personal security.";


    return (
        <div className="flex flex-col items-center justify-center p-6">
            <Fingerprint className="w-16 h-16 text-blue-600 mb-4" />
            <h2 className="text-2xl font-semibold mb-2">{title}</h2>
            <p className="text-center mb-4">{instruction}</p>
            <div className="w-full max-w-md mb-6">
                <video controls className="w-full rounded-lg shadow">
                    <source src="/fingerprint-tutorial.mp4" type="video/mp4" />
                    {language === "vi"
                        ? "Trình duyệt của bạn không hỗ trợ video."
                        : "Your browser does not support the video tag."}
                </video>
            </div>
            <button
                onClick={() => alert("Fingerprint captured!")}
                className="px-4 py-2 bg-blue-600 text-white rounded"
            >
                {captureButtonText}
            </button>
            <div className="mt-6 w-full">
                <Slogan message={sloganMessage} language={language} />
            </div>
        </div>
    );
}
