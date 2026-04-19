import { useState, useRef, useEffect } from "react";
import axios from "axios";
import { useDispatch, useSelector } from "react-redux";
import { updateInteraction } from "../redux/store";

const API_BASE_URL = process.env.REACT_APP_API_URL || "http://127.0.0.1:8000";

export default function Chat() {
  const [message, setMessage] = useState("");
  const [chatHistory, setChatHistory] = useState([
    {
      role: "assistant",
      text: 'Log interaction details here. Example: "Met Dr. Smith, discussed product efficacy, positive sentiment, shared brochures."',
      muted: true,
    },
  ]);
  const [loading, setLoading] = useState(false);

  const dispatch = useDispatch();
  const interaction = useSelector((state) => state.interaction);

  const chatEndRef = useRef(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatHistory]);

  const sendMessage = async () => {
    if (!message.trim() || loading) return;

    const outgoingMessage = message;
    setChatHistory((prev) => [...prev, { role: "user", text: outgoingMessage }]);
    setMessage("");
    setLoading(true);

    try {
      const res = await axios.post(`${API_BASE_URL}/chat`, {
        message: outgoingMessage,
        interaction,
      });

      const payload = res.data;

      if (payload.interaction) {
        dispatch(updateInteraction(payload.interaction));
      }

      const assistantText =
        payload.tool === "log_interaction"
          ? "Interaction logged successfully! The details have been automatically populated based on your summary. Would you like me to suggest a specific follow-up action, such as scheduling a meeting?"
          : payload.tool === "edit_interaction"
            ? "The interaction has been updated with your corrections."
            : payload.assistant_message || "Interaction updated successfully.";

      setChatHistory((prev) => [
        ...prev,
        {
          role: "assistant",
          text: assistantText,
          tool: payload.tool,
          results: payload.results || [],
        },
      ]);
    } catch (err) {
      setChatHistory((prev) => [
        ...prev,
        {
          role: "assistant",
          text: "The assistant could not process that request. Check the FastAPI service and try again.",
        },
      ]);
    }

    setLoading(false);
  };

  return (
    <section className="chat-panel">
      <div className="chat-panel-scroll">
        <div className="chat-header">
          <div>
            <h2>AI Assistant</h2>
            <p>Log Interaction details here via chat</p>
          </div>
        </div>

        <div className="chat-body">
          {chatHistory.map((msg, i) => (
            <div key={`${msg.role}-${i}`} className={`message-row ${msg.role === "user" ? "is-user" : "is-assistant"}`}>
              {msg.results?.length ? (
                <div className="search-result-card">
                  <div className="message-meta">
                    <span className="message-role">Assistant</span>
                  </div>
                  <p className="message-text">{msg.text}</p>
                  {msg.results.map((item) => (
                    <div key={`${item.id || item.hcp_name}-${item.date}-${item.time}`} className="search-result-item">
                      <strong>{item.hcp_name}</strong>
                      <span>{item.date} at {item.time}</span>
                      <p>{item.topics || item.summary || "No summary available."}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <div className={`message-bubble ${msg.muted ? "is-muted" : ""}`}>
                  <div className="message-meta">
                    <span className="message-role">{msg.role === "user" ? "Field Rep" : "Assistant"}</span>
                  </div>
                  <p className={`message-text ${msg.tool === "log_interaction" ? "success-text" : ""}`}>{msg.text}</p>
                </div>
              )}
            </div>
          ))}

          {loading ? (
            <div className="message-row is-assistant">
              <div className="message-bubble is-muted">
                <div className="typing-indicator">
                  <span />
                  <span />
                  <span />
                </div>
              </div>
            </div>
          ) : null}

          <div ref={chatEndRef} />
        </div>
      </div>

      <div className="chat-composer">
        <input
          className="chat-input"
          value={message}
          disabled={loading}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Describe interaction..."
          onKeyDown={(event) => {
            if (event.key === "Enter") {
              event.preventDefault();
              sendMessage();
            }
          }}
        />
        <button className="chat-submit" onClick={sendMessage} disabled={loading}>
          <span>AI</span>
          <span>Log</span>
        </button>
      </div>
    </section>
  );
}