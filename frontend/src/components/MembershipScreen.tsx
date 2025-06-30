import { Slogan } from "./Slogan";
import { useEffect } from "react";
import { playSound, stopSound } from "../utils/playSound";

interface MembershipScreenProps {
    formData: {
        customerType: string; // Expected values: "returning", "new", or others
        fullName: string;
        phoneNumber: string;
        service: string;
        membership: string;
        // THÊM CÁC TRƯỜNG MỚI ĐỂ LƯU GIÁ ĐÃ TÍNH TOÁN
        membershipPriceFormatted?: string; // Giá cuối cùng đã định dạng
        membershipStandardPriceFormatted?: string; // Giá chuẩn đã định dạng (nếu có giảm giá promo)
        [key: string]: any;
    };
    updateFormData: (field: string, value: string) => void;
    nextStep: () => void;
    prevStep: () => void;
    language: string;
}

// --- Pricing Constants ---
const BASE_MONTHLY_PRICE_VND = 600000;
const DAILY_PRICE_VND = 60000;

const DURATION_IN_MONTHS: { [key: string]: number } = {
    "1 month": 1,
    "3 months": 3,
    "6 months": 6,
    "1 year": 12,
};

const STANDARD_DURATION_DISCOUNTS: { [key: string]: number } = {
    "1 month": 0,
    "3 months": 0.10, // 10%
    "6 months": 0.15, // 15%
    "1 year": 0.20,  // 20%
};

const YOGA_BASE_PRICES: { [key: string]: number } = {
    "1 month": 600000,
    "3 months": 1620000,
    "6 months": 3060000,
    "1 year": 5760000,
};

const formatVND = (value: number): string => {
    return new Intl.NumberFormat('de-DE').format(value) + " VND";
};

interface MembershipPriceDetails {
    standardPriceFormatted: string; // Price after standard duration discount (the crossed-out price)
    finalPriceFormatted: string;    // Final price after all discounts
    hasPromotionalDiscount: boolean; // True if a promotional discount was applied (implies standard price shown)
    displayedDiscountPercentage: number; // Percentage discount applied *after* standard duration discount
}
// --- End Pricing Constants ---

export function MembershipScreen({
                                     formData,
                                     updateFormData,
                                     nextStep,
                                     prevStep,
                                     language,
                                 }: MembershipScreenProps) {

    const getMembershipDescription = (id: string, service: string, lang: string) => {
        if (service === "yoga") {
            switch (id) {
                case "1 month":
                    return lang === "en" ? "12 Yoga sessions" : "12 buổi tập Yoga";
                case "3 months":
                    return lang === "en" ? "36 Yoga sessions" : "36 buổi tập Yoga";
                case "6 months":
                    return lang === "en" ? "72 Yoga sessions" : "72 buổi tập Yoga";
                case "1 year":
                    return lang === "en" ? "144 Yoga sessions" : "144 buổi tập Yoga";
                default:
                    return lang === "en" ? "Yoga sessions" : "Buổi tập Yoga";
            }
        } else {
            switch (id) {
                case "1 day":
                    return lang === "en" ? "Single day access" : "Sử dụng trong 1 ngày";
                case "1 month":
                    return lang === "en" ? "30 days of access" : "Sử dụng trong 30 ngày";
                case "3 months":
                    return lang === "en" ? "90 days of access" : "Sử dụng trong 90 ngày";
                case "6 months":
                    return lang === "en" ? "180 days of access" : "Sử dụng trong 180 ngày";
                case "1 year":
                    return lang === "en" ? "365 days of access" : "Sử dụng trong 365 ngày";
                default:
                    return lang === "en" ? "Days of access" : "Ngày sử dụng";
            }
        }
    };

    const calculateMembershipPrice = (membershipId: string, customerType: string, service?: string): MembershipPriceDetails => {
        if (service === "yoga") {
            const basePrice = YOGA_BASE_PRICES[membershipId];
            if (!basePrice) {
                const notAvailable = language === "en" ? "N/A" : "Không có giá";
                return {
                    standardPriceFormatted: notAvailable,
                    finalPriceFormatted: notAvailable,
                    hasPromotionalDiscount: false,
                    displayedDiscountPercentage: 0,
                };
            }
            return {
                standardPriceFormatted: formatVND(basePrice),
                finalPriceFormatted: formatVND(basePrice),
                hasPromotionalDiscount: false,
                displayedDiscountPercentage: 0,
            };
        }
        if (membershipId === '1 day') {
            const dayPassPrice = 60000;
            return {
                standardPriceFormatted: formatVND(dayPassPrice),
                finalPriceFormatted: formatVND(dayPassPrice),
                hasPromotionalDiscount: false,
                displayedDiscountPercentage: 0,
            };
        }
        const months = DURATION_IN_MONTHS[membershipId];
        if (months === undefined) {
            const notAvailable = language === "en" ? "N/A" : "Không có giá";
            return {
                standardPriceFormatted: notAvailable,
                finalPriceFormatted: notAvailable,
                hasPromotionalDiscount: false,
                displayedDiscountPercentage: 0,
            };
        }
        const totalGrossPrice = BASE_MONTHLY_PRICE_VND * months;
        // Apply standard duration discount
        const standardDiscountRate = STANDARD_DURATION_DISCOUNTS[membershipId] ?? 0;
        const priceAfterStandardDiscount = totalGrossPrice * (1 - standardDiscountRate);
        // Không còn áp dụng promotional discount nữa
        // let promotionalDiscountRate = 0;
        // if (customerType === "returning" && PROMO_DISCOUNTS_OLD_CUSTOMER[membershipId] !== undefined) {
        //     promotionalDiscountRate = PROMO_DISCOUNTS_OLD_CUSTOMER[membershipId];
        // } else if (customerType === "new" && PROMO_DISCOUNTS_NEW_CUSTOMER[membershipId] !== undefined) {
        //     promotionalDiscountRate = PROMO_DISCOUNTS_NEW_CUSTOMER[membershipId];
        // }
        // const finalPrice = priceAfterStandardDiscount * (1 - promotionalDiscountRate);
        // const displayedDiscountPercentage = promotionalDiscountRate * 100;
        // const hasPromo = promotionalDiscountRate > 0;
        // return {
        //     standardPriceFormatted: formatVND(Math.round(priceAfterStandardDiscount)),
        //     finalPriceFormatted: formatVND(Math.round(finalPrice)),
        //     hasPromotionalDiscount: hasPromo,
        //     displayedDiscountPercentage: Math.round(displayedDiscountPercentage),
        // };
        // Chỉ áp dụng standard discount
        return {
            standardPriceFormatted: formatVND(Math.round(priceAfterStandardDiscount)),
            finalPriceFormatted: formatVND(Math.round(priceAfterStandardDiscount)),
            hasPromotionalDiscount: false,
            displayedDiscountPercentage: 0,
        };
    };

    let initialMemberships = [
        { id: "1 day", name: language === "en" ? "1 Day" : "Gói 1 Ngày" },
        { id: "1 month", name: language === "en" ? "1 Month" : "Gói 1 Tháng" },
        { id: "3 months", name: language === "en" ? "3 Months" : "Gói 3 Tháng" },
        { id: "6 months", name: language === "en" ? "6 Months" : "Gói 6 Tháng" },
        { id: "1 year", name: language === "en" ? "1 Year" : "Gói 1 Năm" },
    ];

    if (formData.service === "yoga") {
        initialMemberships = initialMemberships.filter((item) => item.id !== "1 day");
    }

    const handleSelect = (membershipId: string) => {
        // Tính toán chi tiết giá cho gói tập đã chọn
        const priceDetails = calculateMembershipPrice(membershipId, formData.customerType, formData.service);

        // Cập nhật formData với ID gói tập và các thông tin giá
        updateFormData("membership", membershipId);
        updateFormData("membershipPriceFormatted", priceDetails.finalPriceFormatted);
        updateFormData("membershipStandardPriceFormatted", priceDetails.standardPriceFormatted);

        // Chuyển sang bước tiếp theo
        nextStep();
    };

    useEffect(() => {
        stopSound();
        playSound(5, language);
        return () => { stopSound(); };
    }, [language]);

    return (
        <div className="space-y-6">
            <h2 className="text-xl font-semibold text-gray-800">
                {language === "en" ? "Choose a Membership" : "Chọn Gói Tập"}
            </h2>
            <p className="text-gray-600">
                {language === "en"
                    ? `Select the membership package that suits you best.`
                    : `Chọn gói tập phù hợp với bạn.`}
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {initialMemberships.map((membership) => {
                    const priceDetails = calculateMembershipPrice(membership.id, formData.customerType, formData.service);
                    return (
                        <button
                            key={membership.id}
                            onClick={() => handleSelect(membership.id)}
                            className={`p-4 border rounded-lg flex flex-col items-center justify-between text-center transition-all hover:bg-blue-50 h-full ${
                                formData.membership === membership.id
                                    ? "border-blue-500 bg-blue-50"
                                    : "border-gray-200"
                            }`}
                        >
                            <span className="font-medium text-gray-800 block mb-2">{membership.name}</span>

                            <div className="flex flex-col items-center my-1">
                                {/* Chỉ hiển thị icon giảm giá nếu có Promotional Discount được áp dụng */}
                                {priceDetails.hasPromotionalDiscount ? (
                                    <>
                                        <div className="flex items-center justify-center gap-1">
                                            <span className="text-xs text-gray-500 line-through">
                                                {priceDetails.standardPriceFormatted}
                                            </span>
                                            <span
                                                className="px-2 py-0.5 text-xs font-semibold text-white bg-red-500 rounded-full"
                                                title={language === "en" ? `Discount: ${priceDetails.displayedDiscountPercentage}%` : `Giảm giá: ${priceDetails.displayedDiscountPercentage}%`}
                                            >
                                                -{priceDetails.displayedDiscountPercentage}%
                                            </span>
                                        </div>
                                        <span className="text-lg font-bold text-green-600 mt-1">
                                            {priceDetails.finalPriceFormatted}
                                        </span>
                                    </>
                                ) : (
                                    // Nếu không có promotional discount, chỉ hiển thị giá cuối cùng (đã bao gồm standard discount nếu có)
                                    <span className="text-lg font-bold text-blue-600">
                                        {priceDetails.finalPriceFormatted}
                                    </span>
                                )}
                            </div>

                            <span className="text-sm text-gray-500 mt-1 block">
                                {getMembershipDescription(membership.id, formData.service, language)}
                            </span>
                        </button>
                    );
                })}
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
                        ? "Remember to turn off lights and equipment when not in use. Let's save energy together!"
                        : "Hãy nhớ tắt đèn và thiết bị điện khi không sử dụng. Cùng nhau tiết kiệm điện!"
                }
                language={language}
            />
        </div>
    );
}