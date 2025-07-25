"use client";
import { useState } from "react";
import api from "@/services/api";
import styles from "./Chat.module.scss";

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

interface ChatRequest {
  message: string;
  conversation_history?: ChatMessage[];
}

interface ChatResponse {
  response: string;
  success: boolean;
  error?: string;
}

export default function Chat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const sendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      role: "user",
      content: inputMessage.trim(),
      timestamp: new Date(),
    };

    // Add user message to chat
    setMessages((prev) => [...prev, userMessage]);
    setInputMessage("");
    setIsLoading(true);

    try {
      const request: ChatRequest = {
        message: userMessage.content,
        conversation_history: messages.slice(-10), // Keep last 10 messages for context
      };

      const response = await api.post<ChatResponse>("/api/chat/chat", request);

      if (response.data.success) {
        const assistantMessage: ChatMessage = {
          role: "assistant",
          content: response.data.response,
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, assistantMessage]);
      } else {
        const errorMessage: ChatMessage = {
          role: "assistant",
          content: "Sorry, I encountered an error processing your request.",
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, errorMessage]);
      }
    } catch (error) {
      console.error("Chat error:", error);
      const errorMessage: ChatMessage = {
        role: "assistant",
        content:
          "Sorry, I could not connect to the chat service. Please try again.",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const clearChat = () => {
    setMessages([]);
  };

  const formatTimestamp = (timestamp: Date) => {
    return timestamp.toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  return (
    <div className={styles.chat}>
      <div className={styles.header}>
        <h2>AppPulse AI Assistant</h2>
        <p>
          Ask me about your API health, system performance, errors, and more!
        </p>
        {messages.length > 0 && (
          <button onClick={clearChat} className={styles.clearButton}>
            Clear Chat
          </button>
        )}
      </div>

      <div className={styles.messageContainer}>
        {messages.length === 0 ? (
          <div className={styles.welcomeMessage}>
            <h3>👋 Welcome to AppPulse AI!</h3>
            <p>
              I can help you understand your application's health and
              performance. Try asking:
            </p>
            <ul>
              <li>"How is my API performing today?"</li>
              <li>"Are there any errors I should be concerned about?"</li>
              <li>"What's my system resource usage looking like?"</li>
              <li>"Which endpoints are the slowest?"</li>
              <li>"Give me an overall health summary"</li>
            </ul>
          </div>
        ) : (
          <div className={styles.messages}>
            {messages.map((message, index) => (
              <div
                key={index}
                className={`${styles.message} ${
                  message.role === "user"
                    ? styles.userMessage
                    : styles.assistantMessage
                }`}
              >
                <div className={styles.messageHeader}>
                  <span className={styles.role}>
                    {message.role === "user" ? "👤 You" : "🤖 AppPulse AI"}
                  </span>
                  <span className={styles.timestamp}>
                    {formatTimestamp(message.timestamp)}
                  </span>
                </div>
                <div className={styles.messageContent}>{message.content}</div>
              </div>
            ))}
            {isLoading && (
              <div className={`${styles.message} ${styles.assistantMessage}`}>
                <div className={styles.messageHeader}>
                  <span className={styles.role}>🤖 AppPulse AI</span>
                </div>
                <div className={styles.messageContent}>
                  <div className={styles.typing}>
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      <div className={styles.inputContainer}>
        <div className={styles.inputWrapper}>
          <textarea
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask me about your metrics... (Press Enter to send)"
            disabled={isLoading}
            rows={2}
          />
          <button
            onClick={sendMessage}
            disabled={!inputMessage.trim() || isLoading}
            className={styles.sendButton}
          >
            {isLoading ? "⏳" : "📤"}
          </button>
        </div>
      </div>
    </div>
  );
}
