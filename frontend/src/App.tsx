import { useState } from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { CustomerTypeScreen } from "./components/CustomerTypeScreen";
import { NameScreen } from "./components/NameScreen";
import { PhoneScreen } from "./components/PhoneScreen";
import { ServiceScreen } from "./components/ServiceScreen";
import { MembershipScreen } from "./components/MembershipScreen";
import { PaymentScreen } from "./components/PaymentScreen";
import { ConfirmationScreen } from "./components/ConfirmationScreen";
import { ProgressBar } from "./components/ProgressBar";
import { LanguageSelector } from "./components/LanguageSelector";
import { IntroScreen } from "./components/IntroScreen";
import { CheckInfoScreen } from "./components/CheckInfoScreen";
import { GuideScreen } from "./components/GuideScreen";
import { FaceId } from "./components/FaceId";
import Loader from "./components/Loader";

export function App() {
  const [step, setStep] = useState(0);
  const [language, setLanguage] = useState("en");
  const [formData, setFormData] = useState({
    customerType: "",
    fullName: "",
    phoneNumber: "",
    service: "",
    membership: ""
  });

  const updateFormData = (field: string, value: any) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const playSoundEffect = () => {
    const audio = new Audio('/s.mp3');
    audio.play();
  };

  const nextStep = () => {
    playSoundEffect();
    setStep((prev) => prev + 1);
  };

  const prevStep = () => {
    playSoundEffect();
    setStep((prev) => prev - 1);
  };

  const totalSteps =
      formData.customerType === "returning" ? 6 : formData.customerType === "new" ? 7 : 0;

  const checkUserInfo = async (phone: string) => {
    // SỬA Ở ĐÂY: Dùng đường dẫn tương đối
    const response = await fetch("/api/app1/check-phone", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ phone })
    });
    if (!response.ok) {
      throw new Error(language === "en" ? "User information not found" : "Không tìm thấy thông tin");
    }
    return await response.json();
  };

  const handleProcessFace = async (phone: string): Promise<{ name: string; phone: string; status: string } | null> => {
    try {
      // SỬA Ở ĐÂY: Dùng đường dẫn tương đối
      const response = await fetch('/api/app5/initiate-faceid', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ phone }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        console.error('Lỗi gọi Flask /initiate-faceid:', errorData);
        return { name: '', phone: '', status: 'error' };
      }

      const data = await response.json();
      return data as { name: string; phone: string; status: string };
    } catch (error: any) {
      console.error('Lỗi fetch /initiate-faceid:', error);
      return { name: '', phone: '', status: 'error' };
    }
  };

  const handleIntroAction = (action: string) => {
    if (action === "register") {
      setStep(1);
    } else if (action === "check") {
      setStep(10);
    } else if (action === "guide") {
      setStep(20);
    } else if (action === "faceid") {
      setStep(30);
    }
  };

  const handleProcessPhoneNumber = async (phone: string): Promise<'found' | 'not_found' | 'error'> => {
    try {
      // SỬA Ở ĐÂY: Dùng đường dẫn tương đối
      const postResponse = await fetch('/api/app4/process-phone-from-screen', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ phoneNumber: phone, customerType: formData.customerType }),
      });

      if (!postResponse.ok) {
        const errorText = await postResponse.text();
        console.error('Lỗi POST lên Flask:', errorText);
        return 'error';
      }

      return new Promise((resolve) => {
        const intervalId = setInterval(async () => {
          try {
            // SỬA Ở ĐÂY: Dùng đường dẫn tương đối
            const getResponse = await fetch(`/api/app4/check-automation-result/${phone}`);
            if (!getResponse.ok) {
              console.error('Lỗi khi kiểm tra kết quả:', getResponse.status);
              clearInterval(intervalId);
              resolve('error');
              return;
            }
            const data = await getResponse.json();
            if (data?.automation_result) {
              clearInterval(intervalId);
              resolve(data.automation_result as 'found' | 'not_found' | 'error');
            }
          } catch (error: any) {
            console.error('Lỗi khi kiểm tra kết quả:', error);
            clearInterval(intervalId);
            resolve('error');
          }
        }, 1500);

        setTimeout(() => {
          clearInterval(intervalId);
          resolve('error');
        }, 30000);
      });

    } catch (fetchError: any) {
      console.error('Lỗi gọi Flask (POST):', fetchError);
      return 'error';
    }
  };

  const resetToIntro = () => {
    setFormData({
      customerType: "",
      fullName: "",
      phoneNumber: "",
      service: "",
      membership: ""
    });
    setStep(0);
  };

  const resetFormData = () => {
    setFormData({
      customerType: "",
      fullName: "",
      phoneNumber: "",
      service: "",
      membership: ""
    });
  };

  return (
      <BrowserRouter>
        <Routes>
          <Route path="/" element={
            <div className="min-h-screen bg-white pt-3 pl-24 pr-24">
              <header className="w-full">
                <div className="max-w-8xl mx-auto px-6 py-6 flex items-center justify-between">
                  <div className="w-40">
                    <img src="/logo.jpg" alt="HD Fitness & Yoga" className="w-full h-auto" />
                  </div>
                  <LanguageSelector language={language} setLanguage={setLanguage} />
                </div>
              </header>
              <main className="max-w-4xl mx-auto pt-32 pb-16 px-4 transform scale-125 transition-transform duration-300">
                <div className="bg-white rounded-xl shadow-lg overflow-hidden">
                  {step === 0 ? (
                      <div className="p-2">
                        <IntroScreen onRegister={handleIntroAction} language={language} />
                      </div>
                  ) : (
                      <>
                        {step >= 1 && step <= totalSteps && step !== 10 && step !== 20 && step !== 30 && (
                            <div className="bg-blue-600 p-6 text-white">
                              <h1 className="text-2xl font-bold">
                                {language === "en"
                                    ? "New Membership / Membership Renewal"
                                    : "Đăng ký mới / Gia hạn gói tập"}
                              </h1>
                              <ProgressBar currentStep={step} totalSteps={totalSteps} />
                            </div>
                        )}
                        <div className="p-6">
                          {step === 1 && <> {console.log("App.tsx (Step 1 - CustomerTypeScreen):", formData)}  <CustomerTypeScreen formData={formData} updateFormData={updateFormData} nextStep={nextStep} prevStep={prevStep} language={language} /></> }
                          {step === 10 && <CheckInfoScreen language={language} checkUserInfo={checkUserInfo} resetToIntro={resetToIntro} />}
                          {step === 20 && <GuideScreen language={language} resetToIntro={resetToIntro} />}
                          {step === 30 && <FaceId language={language} resetToIntro={resetToIntro} checkUserInfo={handleProcessFace} />}
                          {step === 2 &&<> {console.log("App.tsx (Step 2 - NameScreen):", formData)}  <NameScreen formData={formData} updateFormData={updateFormData} nextStep={nextStep} prevStep={prevStep} language={language} /></> }
                          {step === 3 &&<>{console.log("App.tsx (Step 2 - PhoneScreen):", formData)} <PhoneScreen
                              formData={formData}
                              updateFormData={updateFormData}
                              nextStep={nextStep}
                              prevStep={prevStep}
                              language={language}
                              processPhoneNumber={handleProcessPhoneNumber}
                          /></> }
                          {step === 4 && <> {console.log("App.tsx (Step 4 - ServiceScreen):", formData)} <ServiceScreen formData={formData} updateFormData={updateFormData} nextStep={nextStep} prevStep={prevStep} language={language} /></> }
                          {step === 5 && <> {console.log("App.tsx (Step 5 - MembershipScreen):", formData)} <MembershipScreen formData={formData} updateFormData={updateFormData} nextStep={nextStep} prevStep={prevStep} language={language} /></> }
                          {step === 6 && <> {console.log("App.tsx (Step 6 - PaymentScreen):", formData)} <PaymentScreen formData={formData} updateFormData={updateFormData} nextStep={nextStep} prevStep={prevStep} language={language} resetFormData={resetFormData} resetToIntro={resetToIntro} /></> }
                          {step === 7 && (
                              <>
                                {console.log("App.tsx (Step 7 - ConfirmationScreen):", formData)}
                                <ConfirmationScreen
                                    formData={formData}
                                    updateFormData={updateFormData}
                                    nextStep={nextStep}
                                    language={language}
                                    resetToIntro={resetToIntro}
                                />
                              </>
                          )}
                          {step === 8 && formData.customerType === "new" && (
                              <FaceId language={language} resetToIntro={resetToIntro} checkUserInfo={handleProcessFace} />
                          )}
                        </div>
                      </>
                  )}
                </div>
              </main>
            </div>
          } />
          <Route path="/loader" element={<Loader />} />
        </Routes>
      </BrowserRouter>
  );
}

export default App;