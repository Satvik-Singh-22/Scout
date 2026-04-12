'use client';
import { useState, useEffect, useRef } from 'react';
import { getMessages, streamMessage } from '@/lib/api-client';
import type { Message, ChainOfThought as CoTType } from '@/lib/api-client';
import MessageBubble from './MessageBubble';
import { Send, Bot, ChevronRight } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const SUGGESTED_QUERIES = [
  "Which API endpoints have an average response_time_ms higher than average?",
  "Is there a correlation between latency_ms in the Tyk gateway and specific api_name values?",
  "Which services have reported cpu_usage_pct exceeding 80% in the last hour?",
  "Show the share of transactions by region",
  "Which customers have unusually high refund-to-transaction ratios?"
];
interface Props {
  chatroomId: string;
  userPersona: 'EXECUTIVE' | 'TECHNICAL';
  onPersonaChange?: (persona: 'EXECUTIVE' | 'TECHNICAL') => void;
  initialQuery?: string;
}

function DevIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
      <path
        d="M4 5L1 8l3 3M12 5l3 3-3 3M9 3l-2 10"
        stroke="currentColor"
        strokeWidth="1.4"
        strokeLinecap="round"
      />
    </svg>
  );
}

function MgrIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
      <rect
        x="2"
        y="4"
        width="12"
        height="9"
        rx="1.5"
        stroke="currentColor"
        strokeWidth="1.4"
      />
      <path
        d="M5 4V3a1 1 0 011-1h4a1 1 0 011 1v1"
        stroke="currentColor"
        strokeWidth="1.4"
      />
    </svg>
  );
}

export default function Chatroom({
  chatroomId,
  userPersona,
  onPersonaChange,
  initialQuery,
}: Props) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [isLoadingMessages, setIsLoadingMessages] = useState(true);
  const [streamingContent, setStreamingContent] = useState('');
  const didAutoSend = useRef(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const [randomSuggestions, setRandomSuggestions] = useState<string[]>([]);

  useEffect(() => {
    setRandomSuggestions([...SUGGESTED_QUERIES].sort(() => 0.5 - Math.random()).slice(0, 3));
  }, []);
  useEffect(() => {
    setIsLoadingMessages(true);
    getMessages(chatroomId)
      .then(setMessages)
      .catch(() => { })
      .finally(() => setIsLoadingMessages(false));
  }, [chatroomId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingContent, isStreaming]);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  }, [input]);

  // Auto-send initialQuery from dashboard Quick Ask
  useEffect(() => {
    if (initialQuery && !didAutoSend.current) {
      didAutoSend.current = true;
      handleSendQuery(initialQuery);
    }
  }, [initialQuery]);

  const handleSendQuery = (query: string) => {
    if (!query.trim() || isStreaming) return;
    setIsStreaming(true);
    setStreamingContent('');

    const userMsg: Message = {
      id: Date.now().toString(),
      role: 'USER',
      content: query.trim(),
      chain_of_thought: null,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);

    let accumulated = '';

    const stop = streamMessage(
      chatroomId,
      query.trim(),
      userPersona,
      (chunk) => {
        accumulated += chunk;
        setStreamingContent(accumulated);
      },
      (cot: CoTType) => {
        const assistantMsg: Message = {
          id: (Date.now() + 1).toString(),
          role: 'ASSISTANT',
          content: accumulated,
          chain_of_thought: cot,
          created_at: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, assistantMsg]);
        setStreamingContent('');
        setIsStreaming(false);
      },
      (err) => {
        const assistantMsg: Message = {
          id: (Date.now() + 1).toString(),
          role: 'ASSISTANT',
          content: `Error: ${err}`,
          chain_of_thought: null,
          created_at: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, assistantMsg]);
        setStreamingContent('');
        setIsStreaming(false);
      },
    );

    return () => stop();
  };

  const handleSend = () => {
    if (!input.trim() || isStreaming) return;
    const query = input.trim();
    setInput('');
    handleSendQuery(query);
  };

  const personas = [
    { key: 'TECHNICAL' as const, label: 'Technical', icon: <DevIcon /> },
    { key: 'EXECUTIVE' as const, label: 'Executive', icon: <MgrIcon /> },
  ];

  return (
    <div className="flex flex-col h-full bg-gray-50/50">
      {/* Messages area */}
      <div className="flex-1 overflow-y-auto px-4 py-8">
        <div className="max-w-3xl mx-auto">
          {isLoadingMessages ? (
            <div className="flex flex-col items-center justify-center py-20 text-gray-400 gap-3">
              <div className="w-6 h-6 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
              <p className="text-xs font-medium uppercase tracking-widest">Retrieving history...</p>
            </div>
          ) : messages.length === 0 && !isStreaming && (
            <div className="text-center text-gray-400 py-16">
              <div className="w-16 h-16 bg-white rounded-2xl shadow-sm border border-gray-100 flex items-center justify-center mx-auto mb-4 p-3">
                <img src="/scout_icon.svg" alt="Scout" className="w-full h-full object-contain" />
              </div>
              <p className="text-xl font-bold text-gray-900">Scout Intelligence Portal</p>
              <p className="text-sm mt-1 text-gray-500">
                Ask anything about your processed data and customer insights.
              </p>
              <div className="mt-8 flex flex-wrap justify-center gap-2">
                {randomSuggestions.map(suggestion => (
                  <button
                    key={suggestion}
                    onClick={() => handleSendQuery(suggestion)}
                    className="px-4 py-2 bg-white border border-gray-200 rounded-full text-xs font-medium text-gray-600 hover:border-indigo-300 hover:text-indigo-600 transition-all shadow-sm"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((msg) => (
            <MessageBubble
              key={msg.id}
              message={msg}
              persona={userPersona}
              onResend={handleSendQuery}
            />
          ))}

          {isStreaming && (
            <div className="flex flex-col items-start mb-6">
              <div className="flex items-center gap-2 mb-1.5 ml-1">
                <div className="w-6 h-6 rounded-full bg-indigo-100 flex items-center justify-center p-1">
                  <img src="/scout_icon.svg" alt="Scout" className="w-full h-full object-contain" />
                </div>
                <span className="text-xs font-bold text-gray-900">Scout AI</span>
              </div>

              <div className="w-full max-w-[85%] md:max-w-2xl bg-white border border-gray-200 rounded-2xl rounded-tl-none px-4 py-4 text-sm text-gray-800 shadow-sm relative">
                {!streamingContent ? (
                  <div className="flex items-center gap-2 text-gray-400 font-medium italic">
                    <span className="flex gap-1">
                      <span className="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce [animation-delay:-0.3s]"></span>
                      <span className="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce [animation-delay:-0.15s]"></span>
                      <span className="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce"></span>
                    </span>
                    <span>Thinking...</span>
                  </div>
                ) : (
                  <>
                    <div className="text-[10px] font-bold text-indigo-500 uppercase tracking-widest mb-2 border-b border-gray-100 pb-1">
                      AI Response
                    </div>
                    <div className="prose prose-sm max-w-none prose-p:leading-relaxed">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {streamingContent}
                      </ReactMarkdown>
                    </div>
                    <span className="inline-block w-1 h-4 bg-indigo-500 ml-1 animate-pulse" />
                  </>
                )}
              </div>
            </div>
          )}
          <div ref={bottomRef} className="h-4" />
        </div>
      </div>

      {/* Input area */}
      <div className="border-t border-gray-200 bg-white p-4 pb-6">
        <div className="max-w-3xl mx-auto">
          <div className="relative bg-white border border-gray-200 rounded-2xl shadow-sm focus-within:ring-2 focus-within:ring-indigo-500/20 focus-within:border-indigo-500 transition-all">
            <div className="flex items-center bg-gray-50/50 border-b border-gray-100 px-3 py-2 rounded-t-2xl justify-between">
              <div className="flex items-center gap-1 bg-white border border-gray-200 rounded-lg p-1 shadow-sm">
                {personas.map(p => (
                  <button
                    key={p.key}
                    onClick={() => onPersonaChange?.(p.key)}
                    className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[10px] font-bold transition-all ${userPersona === p.key
                      ? 'bg-indigo-600 text-white shadow-sm'
                      : 'text-gray-500 hover:bg-gray-100'
                      }`}
                  >
                    {p.key === 'TECHNICAL' ? <DevIcon /> : <MgrIcon />}
                    {p.label}
                  </button>
                ))}
              </div>
              <span className="text-[10px] font-bold text-gray-400 uppercase tracking-widest hidden sm:block">
                Secure Data Pipeline
              </span>
            </div>

            <textarea
              ref={textareaRef}
              rows={1}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              placeholder="Ask a question about your data..."
              disabled={isStreaming}
              className="w-full px-4 py-3 bg-transparent text-sm focus:outline-none resize-none min-h-[52px] leading-relaxed disabled:opacity-50"
            />

            <div className="flex items-center justify-between px-3 py-2 border-t border-gray-50">
              <span className="text-[10px] text-gray-400 font-medium italic">
                {input.length > 0 ? `${input.length} characters` : 'Press Enter to send, Shift+Enter for new line'}
              </span>
              <button
                onClick={handleSend}
                disabled={isStreaming || !input.trim()}
                className="flex items-center gap-2 px-4 py-1.5 bg-indigo-600 text-white text-xs font-bold rounded-lg hover:bg-indigo-700 disabled:opacity-40 transition-all shadow-sm active:scale-95"
              >
                Send Query
                <Send size={14} />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
