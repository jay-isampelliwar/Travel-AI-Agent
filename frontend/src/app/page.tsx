"use client";

import type { FormEvent, KeyboardEvent } from "react";
import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  type HotelResultItem,
  HotelSearchResults,
  HotelSearchResultsSkeleton,
} from "../components/HotelSearchResults";

type Message = {
  id: number;
  role: "user" | "assistant";
  content: string;
};

type ChatUiType = "hotel_search_ui" | "None" | string;

type ChatResponse = {
  message: string;
  ui_type: ChatUiType | ChatUiType[];
  data: {
    results?: HotelResultItem[];
    [key: string]: unknown;
  };
  follow_up_questions: string[];
};

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [hotelResults, setHotelResults] = useState<HotelResultItem[] | null>(
    null,
  );
  const [isHotelLoading, setIsHotelLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);

  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({
        behavior: "smooth",
        block: "end",
      });
    }
  }, [messages, isLoading]);

  async function sendMessage(userText: string) {
    const trimmed = userText.trim();
    if (!trimmed || isLoading) return;

    setInput("");

    const userMessage: Message = {
      id: Date.now(),
      role: "user",
      content: trimmed,
    };

    const assistantMessage: Message = {
      id: Date.now() + 1,
      role: "assistant",
      content: "",
    };

    setMessages((prev) => [...prev, userMessage, assistantMessage]);
    setIsLoading(true);

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ message: trimmed }),
      });

      if (!response.ok) {
        throw new Error("Request failed");
      }

      const json = (await response.json()) as ChatResponse;

      const cleanedMessage =
        typeof json.message === "string" ? json.message : String(json.message);

      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMessage.id && msg.role === "assistant"
            ? { ...msg, content: cleanedMessage }
            : msg,
        ),
      );

      const uiTypes = Array.isArray(json.ui_type)
        ? json.ui_type
        : [json.ui_type];
      const hasHotelUi = uiTypes.includes("hotel_search_ui");
      const hotelList = (json.data?.results ?? []) as HotelResultItem[];

      if (hasHotelUi && hotelList.length > 0) {
        setIsHotelLoading(true);
        setHotelResults(null);

        setTimeout(() => {
          setHotelResults(hotelList);
          setIsHotelLoading(false);
        }, 500);
      } else {
        setIsHotelLoading(false);
        setHotelResults(null);
      }
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 2,
          role: "assistant",
          content: "There was an error talking to the backend.",
        },
      ]);
      setHotelResults(null);
      setIsHotelLoading(false);
    } finally {
      setIsLoading(false);
    }
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!input.trim() || isLoading) return;
    await sendMessage(input);
  }

  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      if (!isLoading && input.trim()) {
        void sendMessage(input);
      }
    }
  }

  const QUICK_PROMPTS = [
    "Plan a 10-day trip to Japan in April",
    "Budget weekend getaway in Europe",
    "Best beaches for snorkeling in SE Asia",
  ];

  const PlaneIcon = () => (
    <svg
      width="15"
      height="15"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <line x1="22" y1="2" x2="11" y2="13" />
      <polygon points="22 2 15 22 11 13 2 9 22 2" />
    </svg>
  );

  const GlobeIcon = ({ size = 20 }: { size?: number }) => (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <circle cx="12" cy="12" r="10" />
      <line x1="2" y1="12" x2="22" y2="12" />
      <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
    </svg>
  );

  const SparkleIcon = () => (
    <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 2l2.4 7.4H22l-6.2 4.5 2.4 7.4L12 17l-6.2 4.3 2.4-7.4L2 9.4h7.6z" />
    </svg>
  );

  return (
    <div className="flex h-screen justify-center bg-stone-100 px-4 py-4 overflow-hidden">
      <main className="flex w-full max-w-6xl flex-1 flex-col min-h-0">
        {/* Header */}
        <header className="mb-5 flex items-center justify-between border-b border-stone-200 pb-5">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-neutral-900 text-white">
              <GlobeIcon size={18} />
            </div>
            <div>
              <h1 className="text-[21px] font-semibold tracking-tight text-neutral-900">
                Travel Intelligence
              </h1>
              <p className="text-base text-stone-400">
                Your AI-powered trip planner
              </p>
            </div>
          </div>
          <div className="flex items-center gap-1.5 rounded-full border border-stone-200 bg-white px-3 py-1.5 text-base text-stone-400">
            <SparkleIcon />
            <span>AI-powered</span>
          </div>
        </header>

        {/* Chat window */}
        <section className="flex flex-1 min-h-0 overflow-hidden rounded-2xl border border-stone-200 bg-white shadow-sm">
          {/* Messages */}
          <div className="flex flex-1 min-h-0 flex-col gap-5 overflow-y-auto p-6">
            {messages.length === 0 ? (
              <div className="flex flex-1 flex-col items-center justify-center gap-3 py-12 text-center">
                <div className="flex h-14 w-14 items-center justify-center rounded-2xl border border-stone-200 bg-stone-50 text-stone-400">
                  <GlobeIcon size={22} />
                </div>
                <p className="text-xl font-semibold tracking-tight text-neutral-900">
                  Where to next?
                </p>
                <p className="max-w-[260px] text-lg leading-relaxed text-stone-400">
                  Share your destination, dates, budget, and the kind of
                  experience you&apos;re after.
                </p>
                <div className="mt-2 flex flex-wrap justify-center gap-2">
                  {QUICK_PROMPTS.map((p) => (
                    <button
                      key={p}
                      onClick={() => sendMessage(p)}
                      className="rounded-full border border-stone-200 bg-stone-50 px-3.5 py-1.5 text-base text-stone-500 transition-colors hover:border-stone-300 hover:bg-stone-100 hover:text-neutral-800"
                    >
                      {p}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              messages.map((msg) => {
                if (msg.role === "assistant" && !msg.content.trim()) {
                  return null;
                }

                return (
                  <div
                    key={msg.id}
                    className={`flex items-end gap-2.5 ${
                      msg.role === "user" ? "flex-row-reverse" : "flex-row"
                    }`}
                  >
                    {/* Avatar — assistant only */}
                      {msg.role === "assistant" && (
                      <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg border border-stone-200 bg-stone-50 text-stone-400">
                        <GlobeIcon size={14} />
                      </div>
                    )}

                    <div
                      className={`max-w-[72%] rounded-2xl px-4 py-3 text-lg leading-relaxed ${
                        msg.role === "user"
                          ? "rounded-br-sm bg-neutral-900 text-white"
                          : "rounded-bl-sm border border-stone-200 bg-stone-50 text-neutral-900"
                      }`}
                    >
                      <p
                        className={`mb-1 text-[14px] font-semibold uppercase tracking-widest ${
                          msg.role === "user"
                            ? "text-white/50"
                            : "text-stone-400"
                        }`}
                      >
                        {msg.role === "user" ? "You" : "Assistant"}
                      </p>
                      {msg.role === "assistant" ? (
                        <div className="text-[15px] leading-relaxed">
                          <ReactMarkdown remarkPlugins={[remarkGfm]}>
                            {msg.content}
                          </ReactMarkdown>
                        </div>
                      ) : (
                        <p className="whitespace-pre-wrap">{msg.content}</p>
                      )}
                    </div>
                  </div>
                );
              })
            )}

            {/* Typing indicator */}
            {isLoading && (
              <div className="flex items-end gap-2.5">
                <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg border border-stone-200 bg-stone-50 text-stone-400">
                  <GlobeIcon size={14} />
                </div>
                <div className="rounded-2xl rounded-bl-sm border border-stone-200 bg-stone-50 px-4 py-3.5">
                  <div className="flex gap-1">
                    <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-stone-400 [animation-delay:-0.3s]" />
                    <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-stone-400 [animation-delay:-0.15s]" />
                    <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-stone-400" />
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {isHotelLoading ? (
            <HotelSearchResultsSkeleton />
          ) : (
            hotelResults &&
            hotelResults.length > 0 && (
              <HotelSearchResults results={hotelResults} />
            )
          )}
        </section>

        {/* Input bar */}
        <form
          onSubmit={handleSubmit}
          className="mt-2 flex items-end gap-2.5 rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3.5"
        >
          <textarea
            ref={textareaRef}
            rows={1}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about destinations, itineraries, costs…"
            className="flex-1 resize-none overflow-hidden rounded-xl border border-stone-200 bg-white px-3.5 py-2.5 text-lg text-neutral-900 placeholder:text-stone-300 outline-none transition-colors focus:border-stone-400"
          />
          <button
            type="submit"
            disabled={isLoading || !input.trim()}
            aria-label="Send message"
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-neutral-900 text-white transition-all hover:opacity-80 active:scale-95 disabled:cursor-not-allowed disabled:opacity-30"
          >
            <PlaneIcon />
          </button>
        </form>
      </main>
    </div>
  );
}
