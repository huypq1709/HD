// src/global.d.ts
interface SpeechRecognitionEvent extends Event {
    results: SpeechRecognitionResultList;
    interpretation: any; // Optional, depending on your implementation
}

interface SpeechRecognitionResultList {
    0: SpeechRecognitionResult;
}

interface SpeechRecognitionResult {
    isFinal: boolean;
    length: number;
    0: SpeechRecognitionAlternative;
}

interface SpeechRecognitionAlternative {
    transcript: string;
    confidence: number;
}

interface Window {
    SpeechRecognition: typeof SpeechRecognition;
    webkitSpeechRecognition: typeof webkitSpeechRecognition;
}
