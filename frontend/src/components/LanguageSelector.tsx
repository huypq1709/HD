interface LanguageSelectorProps {
    language: string;
    setLanguage: (lang: string) => void;
}

export function LanguageSelector({ language, setLanguage }: LanguageSelectorProps) {
    return (
        <div className="flex items-center space-x-2">
            <button
                onClick={() => {
                    console.log("Switching to EN");
                    setLanguage("en");
                }}

                className={`flex items-center space-x-1 px-3 py-1.5 rounded ${
                    language === "en" ? "bg-blue-50 text-blue-600" : "text-gray-600 hover:bg-gray-50"
                }`}
                disabled={language === "en"}
            >
                <span>EN</span>
            </button>
            <span className="text-gray-300">|</span>
            <button
                onClick={() => {
                    console.log("Switching to VI");
                    setLanguage("vi");
                }}

                className={`flex items-center space-x-1 px-3 py-1.5 rounded ${
                    language === "vi" ? "bg-blue-50 text-blue-600" : "text-gray-600 hover:bg-gray-50"
                }`}
                disabled={language === "vi"}

            >
                <span>VI</span>
            </button>
            <span className="ml-3 text-sm text-gray-500">Thay đổi ngôn ngữ/ Change Language</span>
        </div>
    );
}
