// File: src/components/ChatbotWidget.tsx

import React, { useState, useEffect, useRef } from 'react';
import styles from './ChatbotWidget.module.css';

// Định nghĩa kiểu dữ liệu cho tin nhắn
interface Message {
  role: 'user' | 'model' | 'system';
  parts: string;
}

const ChatbotWidget: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isFirstMessage, setIsFirstMessage] = useState(true);
  
  const inactivityTimer = useRef<number>();
  const autoCloseTimer = useRef<number>();
  const chatWindowRef = useRef<HTMLDivElement>(null);
  const apiUrl = '/api/app6/chat'; // URL của backend Flask

  // Hàm khởi tạo/reset cuộc trò chuyện
  const initChat = () => {
    setIsFirstMessage(true);
    setMessages([
      {
        role: 'system',
        parts: 'Chào bạn, tôi có thể giúp gì cho bạn hôm nay?<br/>Hello, how can I help you today?',
      },
    ]);
  };
  
  // Hàm reset do không hoạt động
  const resetChat = () => {
    setMessages((prev) => [...prev, { role: 'system', parts: 'Vâng, chào tạm biệt và hẹn gặp lại bạn tại HD Fitness and Yoga!' }]);
    setTimeout(() => {
        initChat();
        setIsOpen(false);
    }, 2000);
  };
  
  // Bộ đếm giờ cho reset do không hoạt động (2 phút)
  const startTimer = () => {
    clearTimeout(inactivityTimer.current);
    inactivityTimer.current = window.setTimeout(resetChat, 2 * 60 * 1000); // 2 phút
  };

  // Bộ đếm giờ tự động reset và thu nhỏ chat nếu không gửi câu hỏi nào (90s)
  const startAutoCloseTimer = () => {
    clearTimeout(autoCloseTimer.current);
    autoCloseTimer.current = window.setTimeout(() => {
      initChat(); // Xóa toàn bộ nội dung chat về tin nhắn chào
      setIsOpen(false); // Thu nhỏ khung chat
    }, 90 * 1000); // 90 giây
  };

  useEffect(() => {
    initChat(); // Khởi tạo chat lần đầu
  }, []);

  // Tự động cuộn xuống tin nhắn mới nhất
  useEffect(() => {
    if (chatWindowRef.current) {
      chatWindowRef.current.scrollTop = chatWindowRef.current.scrollHeight;
    }
  }, [messages]);
  
  // Quản lý bộ đếm giờ
  useEffect(() => {
    if (isOpen) {
      startAutoCloseTimer();
    } else {
      clearTimeout(autoCloseTimer.current);
    }
    return () => clearTimeout(autoCloseTimer.current);
  }, [isOpen]);

  const handleToggleChat = () => {
    setIsOpen(!isOpen);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim()) return;

    const userMessage: Message = { role: 'user', parts: inputValue };
    
    // Xóa tin nhắn chào mừng nếu đây là tin nhắn đầu tiên
    const newMessages = isFirstMessage ? [userMessage] : [...messages, userMessage];
    setIsFirstMessage(false);

    setMessages(newMessages);
    setInputValue('');
    setIsLoading(true);
    clearTimeout(inactivityTimer.current); // Dừng timer khi đang chờ bot trả lời
    clearTimeout(autoCloseTimer.current); // Dừng auto close khi đang gửi câu hỏi

    try {
        const historyForApi = newMessages.slice(0, -1).map(msg => ({
            role: msg.role === 'user' ? 'user' : 'model',
            parts: msg.parts
        }));

        const response = await fetch(apiUrl, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: inputValue,
                history: historyForApi,
            }),
        });
        if (!response.ok) throw new Error('Network response was not ok');
        const data = await response.json();
        setMessages((prev) => [...prev, { role: 'model', parts: data.reply }]);
    } catch (error) {
        console.error('Lỗi:', error);
        setMessages((prev) => [...prev, { role: 'model', parts: 'Rất tiếc, đã có lỗi xảy ra.' }]);
    } finally {
        setIsLoading(false);
        startTimer(); // Khởi động lại timer sau khi bot đã trả lời
        startAutoCloseTimer(); // Khởi động lại auto close timer
    }
  };

  return (
    <div className={`${styles.widgetContainer} ${isOpen ? styles.open : ''}`}>
      <div className={styles.chatContainer}>
        <div className={styles.chatHeader}>HD Fitness & Yoga Assistant</div>
        <div className={styles.chatWindow} ref={chatWindowRef}>
          {messages.map((msg, index) => {
            let messageClass = '';
            if (msg.role === 'user') messageClass = styles.userMessage;
            else if (msg.role === 'model') messageClass = styles.botMessage;
            else if (msg.role === 'system') {
                // Đây là tin nhắn chào mừng hoặc tạm biệt
                messageClass = msg.parts.startsWith('Vâng, chào') ? styles.goodbyeMessage : styles.botMessage;
            }
            return (
              <div key={index} className={`${styles.message} ${messageClass}`} dangerouslySetInnerHTML={{ __html: msg.parts.replace(/\n/g, '<br>') }}>
              </div>
            );
          })}
          {isLoading && (
            <div className={`${styles.message} ${styles.loadingDots}`}>
                <span className={styles.dot1}></span>
                <span className={styles.dot2}></span>
                <span className={styles.dot3}></span>
            </div>
          )}
        </div>
        <form className={styles.chatForm} onSubmit={handleSubmit}>
          <input
            type="text"
            className={styles.messageInput}
            value={inputValue}
            onChange={(e) => {
                setInputValue(e.target.value);
                startTimer(); // Reset timer khi người dùng gõ
            }}
            placeholder="Nhập câu hỏi của bạn/ Ask me anything"
            autoComplete="off"
          />
          <button type="submit">➤</button>
        </form>
      </div>

      <div className={styles.callout}>Tư vấn tại đây / Chat here</div>
      
      <button className={styles.toggleButton} onClick={handleToggleChat}>
        <img src="/chatbot-white.png" alt="Chat Icon" />
      </button>
    </div>
  );
};

export default ChatbotWidget;