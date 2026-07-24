"use client";

import React, { useState, useRef, useEffect } from "react";
import { Send, User, Bot, RefreshCw, Sun, Moon } from "lucide-react";
import { useTheme } from "next-themes";

interface Message {
  id: string;
  sender: "user" | "bot";
  text: string;
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [mounted, setMounted] = useState(false);
  const { theme, setTheme } = useTheme();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Avoid hydration mismatch for theme toggle button
  useEffect(() => {
    setMounted(true);
  }, []);

  const isChatStarted = messages.length > 0;

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    if (isChatStarted) {
      scrollToBottom();
    }
  }, [messages, isLoading, isChatStarted]);

  const handleReset = () => {
    setMessages([]);
    setInput("");
  };

  const handleSend = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const query = input.trim();
    if (!query || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      sender: "user",
      text: query,
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      const backendUrl =
        process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
      const response = await fetch(`${backendUrl}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: query }),
      });

      if (!response.ok) {
        throw new Error(`Server returned status ${response.status}`);
      }

      const data = await response.json();

      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        sender: "bot",
        text: data.answer || "No response received.",
      };

      setMessages((prev) => [...prev, botMessage]);
    } catch (err) {
      console.error(err);
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          sender: "bot",
          text: "⚠️ Connection error: Unable to reach the Factify backend server. Ensure FastAPI is running on port 8000.",
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="flex flex-col h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 overflow-hidden relative transition-colors duration-300">
      {/* Top Header Bar (Appears when conversation starts) */}
      <header
        className={`flex items-center justify-between px-8 py-4 border-b border-slate-200 dark:border-slate-800/80 bg-slate-100/80 dark:bg-slate-950/80 backdrop-blur z-20 transition-all duration-500 ${
          isChatStarted
            ? "opacity-100 translate-y-0"
            : "opacity-0 -translate-y-4 pointer-events-none"
        }`}
      >
        <button
          onClick={handleReset}
          className="text-3xl font-bold tracking-tight transition-transform hover:scale-105 focus:outline-none"
          style={{ color: "#bf45cc" }}
          title="Reset session to Home"
        >
          Factify
        </button>

        <div className="flex items-center gap-3">
          {/* Theme Switcher Button */}
          {mounted && (
            <button
              onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
              className="p-2 rounded-xl text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-800 transition-colors"
              title="Toggle Theme"
            >
              {theme === "dark" ? (
                <Sun className="w-5 h-5" />
              ) : (
                <Moon className="w-5 h-5" />
              )}
            </button>
          )}

          <button
            onClick={handleReset}
            className="p-2 text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 transition-colors flex items-center gap-2 text-sm font-medium"
            title="Clear Chat"
          >
            <RefreshCw className="w-4 h-4" />
            <span>New Chat</span>
          </button>
        </div>
      </header>

      {/* Floating Theme Toggle when on Hero Landing Page */}
      {!isChatStarted && mounted && (
        <div className="absolute top-6 right-8 z-30">
          <button
            onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
            className="p-2.5 rounded-2xl bg-slate-200/60 dark:bg-slate-900/60 border border-slate-300 dark:border-slate-800 text-slate-700 dark:text-slate-300 hover:scale-105 transition-all shadow-sm"
            title="Toggle Theme"
          >
            {theme === "dark" ? (
              <Sun className="w-5 h-5" />
            ) : (
              <Moon className="w-5 h-5" />
            )}
          </button>
        </div>
      )}

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col justify-between overflow-hidden relative">
        {/* LANDING STATE (Hero View - Pre-chat) */}
        {!isChatStarted && (
          <div className="flex-1 flex flex-col items-center justify-center px-4 -mt-12 transition-all duration-500">
            {/* Factify Brand Title in Geist Font */}
            <h1
              className="text-7xl md:text-8xl font-black mb-12 tracking-tight select-none drop-shadow-sm"
              style={{ color: "#bf45cc" }}
            >
              Factify
            </h1>

            {/* Central Pill Search Bar */}
            <form
              onSubmit={handleSend}
              className="w-full max-w-2xl flex items-center gap-3 bg-white dark:bg-slate-900/90 border border-slate-200 dark:border-slate-800 rounded-full px-6 py-4 shadow-xl focus-within:border-[#bf45cc] dark:focus-within:border-[#bf45cc] transition-all duration-300"
            >
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask me anything that you would like to fact-check!"
                className="flex-1 bg-transparent text-slate-900 dark:text-slate-100 placeholder-slate-400 dark:placeholder-slate-500 text-base focus:outline-none"
              />
              <button
                type="submit"
                disabled={!input.trim() || isLoading}
                className="p-3 rounded-full text-white disabled:opacity-40 transition-transform active:scale-95"
                style={{ backgroundColor: "#bf45cc" }}
              >
                <Send className="w-5 h-5" />
              </button>
            </form>
          </div>
        )}

        {/* ACTIVE CHAT FEED */}
        {isChatStarted && (
          <div className="flex-1 overflow-y-auto p-6 space-y-6 max-w-4xl w-full mx-auto">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex items-start gap-4 ${
                  msg.sender === "user" ? "flex-row-reverse" : "flex-row"
                }`}
              >
                <div
                  className={`p-2 rounded-xl border ${
                    msg.sender === "user"
                      ? "text-white border-purple-500/30"
                      : "bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-300 border-slate-200 dark:border-slate-800 shadow-sm"
                  }`}
                  style={{
                    backgroundColor:
                      msg.sender === "user" ? "#bf45cc" : undefined,
                  }}
                >
                  {msg.sender === "user" ? (
                    <User className="w-5 h-5" />
                  ) : (
                    <Bot className="w-5 h-5" />
                  )}
                </div>

                <div
                  className={`max-w-[80%] rounded-2xl px-5 py-3.5 text-sm leading-relaxed ${
                    msg.sender === "user"
                      ? "text-white rounded-tr-none shadow-md"
                      : "bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-800 dark:text-slate-200 rounded-tl-none whitespace-pre-wrap shadow-sm"
                  }`}
                  style={{
                    backgroundColor:
                      msg.sender === "user" ? "#bf45cc" : undefined,
                  }}
                >
                  {msg.text}
                </div>
              </div>
            ))}

            {/* Staggered Bouncing Dots Loading Animation */}
            {isLoading && (
              <div className="flex items-center gap-4 py-2">
                <div className="p-2 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-700 dark:text-slate-300 shadow-sm">
                  <Bot className="w-5 h-5" />
                </div>
                <div className="flex items-center gap-2 px-2 py-1">
                  {/* Dot 1 (Smallest) */}
                  <span
                    className="w-2 h-2 rounded-full animate-dot-1"
                    style={{ backgroundColor: "#bf45cc" }}
                  />
                  {/* Dot 2 (Medium) */}
                  <span
                    className="w-3 h-3 rounded-full animate-dot-2"
                    style={{ backgroundColor: "#bf45cc" }}
                  />
                  {/* Dot 3 (Largest) */}
                  <span
                    className="w-4 h-4 rounded-full animate-dot-3"
                    style={{ backgroundColor: "#bf45cc" }}
                  />
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        )}

        {/* BOTTOM INPUT BAR (Visible in active chat view) */}
        {isChatStarted && (
          <div className="p-4 border-t border-slate-200 dark:border-slate-800/80 bg-slate-100/80 dark:bg-slate-950/80 backdrop-blur z-20">
            <form
              onSubmit={handleSend}
              className="max-w-4xl mx-auto flex items-center gap-3 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-full px-5 py-2.5 focus-within:border-[#bf45cc] dark:focus-within:border-[#bf45cc] transition-colors shadow-sm"
            >
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask me anything that you would like to fact-check!"
                className="flex-1 bg-transparent px-2 text-sm text-slate-900 dark:text-slate-100 placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none"
              />
              <button
                type="submit"
                disabled={!input.trim() || isLoading}
                className="p-2.5 text-white rounded-full disabled:opacity-40 transition-transform active:scale-95"
                style={{ backgroundColor: "#bf45cc" }}
              >
                <Send className="w-4 h-4" />
              </button>
            </form>
          </div>
        )}
      </div>
    </main>
  );
}