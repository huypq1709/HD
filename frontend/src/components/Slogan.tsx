import React from "react";
export function Slogan({
  message,
  language
}) {
  return <div className="mt-6 p-4 bg-blue-50 border border-blue-100 rounded-lg">
      <p className="text-sm text-blue-700 flex items-center justify-center">
        <span className="mr-2">💡</span>
        {message}
      </p>
    </div>;
}