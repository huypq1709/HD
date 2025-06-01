import React from "react";
export function ProgressBar({
  currentStep,
  totalSteps
}) {
  const progress = currentStep / totalSteps * 100;
  return <div className="mt-4">
      <div className="w-full bg-blue-300 rounded-full h-2.5">
        <div className="bg-white h-2.5 rounded-full transition-all duration-300 ease-in-out" style={{
        width: `${progress}%`
      }}></div>
      </div>
      <div className="text-sm mt-2 text-blue-100">
        Step {currentStep} of {totalSteps}
      </div>
    </div>;
}