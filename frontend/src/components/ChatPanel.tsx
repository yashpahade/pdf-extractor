import { useState, useRef, useEffect } from "react";
import { chatWithDocument, type ChatResponse } from "../api/chat";

interface Message {
  role: "user" | "assistant";
  content: string;
  tokens?: number;
  provider?: string;
}

interface Props {
  documentId: number | null;
}

export default function ChatPanel({ documentId }: Props) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Reset chat when document changes
  useEffect(() => {
    setMessages([]);
  }, [documentId]);

  const handleSend = async () => {
    if (!input.trim() || !documentId || loading) return;

    const query = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: query }]);
    setLoading(true);

    try {
      const response = await chatWithDocument({
        query,
        document_id: documentId,
      });

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: response.answer,
          tokens: response.tokens_used,
          provider: response.provider,
        },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `Error: ${err instanceof Error ? err.message : "Failed to get response"}`,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  if (!documentId) {
    return (
      <div className="chat-panel chat-panel--disabled">
        <p>Select a document to start asking questions</p>
      </div>
    );
  }

  return (
    <div className="chat-panel">
      <div className="chat-panel__header">
        <h3>💬 Ask about this document</h3>
      </div>

      <div className="chat-panel__messages">
        {messages.length === 0 && (
          <p className="chat-panel__hint">
            Ask any question about the uploaded document.
          </p>
        )}
        {messages.map((msg, i) => (
          <div key={i} className={`chat-msg chat-msg--${msg.role}`}>
            <div className="chat-msg__content">{msg.content}</div>
            {msg.tokens && (
              <span className="chat-msg__meta">
                {msg.tokens} tokens · {msg.provider}
              </span>
            )}
          </div>
        ))}
        {loading && (
          <div className="chat-msg chat-msg--assistant">
            <div className="chat-msg__content chat-msg--loading">
              Thinking…
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="chat-panel__input">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type your question…"
          disabled={loading}
        />
        <button
          className="btn btn--primary"
          onClick={handleSend}
          disabled={loading || !input.trim()}
        >
          Send
        </button>
      </div>
    </div>
  );
}
