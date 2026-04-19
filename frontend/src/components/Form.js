import { useSelector } from "react-redux";

export default function Form() {
  const data = useSelector((state) => state.interaction);
  const materials = data.materials_shared || [];
  const samples = data.samples_distributed || [];
  const suggestions = data.ai_suggested_follow_up || [];

  return (
    <section className="interaction-panel">
      <div className="interaction-panel-scroll">
        <h1 className="panel-title">Log HCP Interaction</h1>

        <div className="panel-heading">
          <div>
            <h2>Interaction Details</h2>
          </div>
        </div>

        <div className="field-grid two-up compact-gap">
          <div className="field-block">
            <label>HCP Name</label>
            <input
              className="readonly-input"
              value={data.hcp_name || ""}
              placeholder="Search or select HCP..."
              readOnly
            />
          </div>

          <div className="field-block">
            <label>Interaction Type</label>
            <div className="readonly-select">
              <input
                className="readonly-input with-icon"
                value={data.interaction_type || ""}
                placeholder="Meeting"
                readOnly
              />
              <span className="field-icon">▾</span>
            </div>
          </div>
        </div>

        <div className="field-grid two-up compact-gap">
          <div className="field-block">
            <label>Date</label>
            <div className="readonly-select">
              <input className="readonly-input with-icon" value={data.date || ""} placeholder="04/19/2025" readOnly />
              <span className="field-icon">◷</span>
            </div>
          </div>

          <div className="field-block">
            <label>Time</label>
            <div className="readonly-select">
              <input className="readonly-input with-icon" value={data.time || ""} placeholder="07:36 PM" readOnly />
              <span className="field-icon">◔</span>
            </div>
          </div>
        </div>

        <div className="field-block">
          <label>Attendees</label>
          <input
            className="readonly-input"
            value={data.attendees || ""}
            placeholder="Enter names or search..."
            readOnly
          />
        </div>

        <div className="field-block">
          <label>Topics Discussed</label>
          <textarea
            className="readonly-textarea"
            value={data.topics || ""}
            placeholder="Enter key discussion points..."
            readOnly
          />
        </div>

        <button className="secondary-inline-action" type="button" disabled>
          Summarize from Voice Note (Requires Consent)
        </button>

        <div className="field-block">
          <label>Materials Shared / Samples Distributed</label>
          <div className="collection-stack">
            <div className="collection-card">
              <div className="collection-header">
                <span>Materials Shared</span>
                <button type="button" disabled>
                  Search/Add
                </button>
              </div>
              <p>{materials.length ? materials.join(", ") : "No materials added."}</p>
            </div>

            <div className="collection-card">
              <div className="collection-header">
                <span>Samples Distributed</span>
                <button type="button" disabled>
                  Add Sample
                </button>
              </div>
              <p>{samples.length ? samples.join(", ") : "No samples added."}</p>
            </div>
          </div>
        </div>

        <div className="field-block">
          <label>Observed/ Inferred HCP Sentiment</label>

          <div className="sentiment-row">
            {["positive", "neutral", "negative"].map((type) => (
              <label
                key={type}
                className={`sentiment-option ${data.sentiment?.toLowerCase() === type ? "is-active" : ""}`}
              >
                <span className="sentiment-radio">
                  <span className="sentiment-radio-fill" />
                </span>
                <span className="sentiment-emoji">
                  {type === "positive" && "🙂"}
                  {type === "neutral" && "😐"}
                  {type === "negative" && "🙁"}
                </span>
                <span>{type.charAt(0).toUpperCase() + type.slice(1)}</span>
              </label>
            ))}
          </div>
        </div>

        <div className="field-block">
          <label>Summary</label>
          <textarea
            className="readonly-textarea"
            value={data.outcomes || data.summary || ""}
            placeholder="Interaction summary..."
            readOnly
          />
        </div>

        <div className="field-block">
          <label>Follow-up Actions</label>
          <textarea
            className="readonly-textarea"
            value={data.follow_up || ""}
            placeholder="Enter next steps or tasks..."
            readOnly
          />
        </div>

        <div className="field-block">
          <label>AI Suggested Follow-up</label>
          <div className="suggestion-card">
            {suggestions.length ? (
              suggestions.map((item) => (
                <p key={item}>- {item}</p>
              ))
            ) : (
              <p>Ask the assistant to suggest next-best actions.</p>
            )}
          </div>
        </div>

        <div className="field-grid two-up">
          <div className="field-block">
            <label>AI Insight</label>
            <textarea
              className="readonly-textarea compact"
              value={data.insight || ""}
              placeholder="Commercial or engagement insight..."
              readOnly
            />
          </div>

          <div className="field-block">
            <label>Priority</label>
            <input
              className="readonly-input"
              value={data.priority || ""}
              placeholder="low / medium / high"
              readOnly
            />
          </div>
        </div>
      </div>
    </section>
  );
}
