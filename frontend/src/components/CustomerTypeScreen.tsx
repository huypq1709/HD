import React from "react";
import { UserIcon, UserPlusIcon } from "lucide-react";
import { Slogan } from "./Slogan";

interface CustomerTypeScreenProps {
    formData: {
        customerType: string;
        fullName: string;
        phoneNumber: string;
        service: string;
        membership: string;
    };
    updateFormData: (field: string, value: any) => void;
    nextStep: () => void;
    prevStep: () => void;
    language: string;
}

export const CustomerTypeScreen: React.FC<CustomerTypeScreenProps> = ({
                                                                          formData,
                                                                          updateFormData,
                                                                          nextStep,
                                                                          prevStep,
                                                                          language,
                                                                      }) => {
    const handleSelect = (type: string) => {
        updateFormData("customerType", type);
        nextStep();
    };

    return (
        <div className="space-y-6">
            <h2 className="text-xl font-semibold text-gray-800">
                {language === "en" ? "Welcome!" : "Chào mừng!"}
            </h2>
            <p className="text-gray-600">
                {language === "en" ? "Are you a first-time visitor or returning customer?" : "Bạn là khách hàng mới hay khách hàng cũ?"}
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <button
                    onClick={() => handleSelect("new")}
                    className={`p-6 border rounded-lg flex flex-col items-center transition-all hover:bg-blue-50 ${formData.customerType === "new" ? "border-blue-500 bg-blue-50" : "border-gray-200"}`}
                >
                    <UserPlusIcon className="h-12 w-12 mb-2 text-blue-500" />
                    <span className="font-medium text-gray-800" >{language === "en" ? "New Customer" : "Khách hàng mới"}</span>
                </button>
                <button
                    onClick={() => handleSelect("returning")}
                    className={`p-6 border rounded-lg flex flex-col items-center transition-all hover:bg-blue-50 ${formData.customerType === "returning" ? "border-blue-500 bg-blue-50" : "border-gray-200"}`}
                >
                    <UserIcon className="h-12 w-12 mb-2 text-blue-500" />
                    <span className="font-medium text-gray-800">{language === "en" ? "Returning Customer" : "Khách hàng cũ "}</span>
                </button>
            </div>
            <div className="flex justify-between pt-4">
                <button
                    type="button"
                    onClick={prevStep}
                    className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                    {language === "en" ? "Back" : "Trở lại"}
                </button>
            </div>
            <Slogan
                message={language === "en" ? "Welcome to the gym! Remember to bring your towel and water bottle." : "Chào mừng bạn đến với phòng tập! Hãy nhớ mang theo khăn và bình nước nhé."}
                language={language}
            />
        </div>
    );
};