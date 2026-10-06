import { useState } from "react";
import { type DocumentMeta, resummarize } from "../api/documents";

interface Props {
  document: DocumentMeta | null;
  onDocumentUpdated: (doc: DocumentMeta) => void;
}

export default function SummaryViewer({ document, onDocumentUpdated }: Props) {
  const [copied, setCopied] = useState(false);
  const [resummarizing, setResummarizing] = useState(false);

  if (!document) {
    return (
      <div className="summary-empty">
        <div className="summary-empty__icon">📋</div>
        <h2>Select a document</h2>
        <p>Upload a file or select one from the sidebar to view its summary.</p>
      </div>
    );
  }

  const handleCopy = async () => {
    if (document.summary) {
      await navigator.clipboard.writeText(document.summary);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleResummarize = async () => {
    setResummarizing(true);
    try {
      const updated = await resummarize(document.id);
      onDocumentUpdated(updated);
    } catch {
      // Error handled by caller
    } finally {
      setResummarizing(false);
    }
  };

  return (
    <div className="summary-viewer">
      <header className="summary-viewer__header">
        <div>
          <h2 className="summary-viewer__title">{document.filename}</h2>
          <div className="summary-viewer__meta">
            {document.page_count && (
              <span>{document.page_count} pages</span>
            )}
            {document.tokens_used > 0 && (
              <span>{document.tokens_used.toLocaleString()} tokens</span>
            )}
            {document.processing_time_ms && (
              <span>
                {(document.processing_time_ms / 1000).toFixed(1)}s
              </span>
            )}
            {document.provider_used && (
              <span className="badge badge--info">
                {document.provider_used}
              </span>
            )}
          </div>
        </div>
        <div className="summary-viewer__actions">
          {document.summary && (
            <button
              className="btn btn--secondary"
              onClick={handleCopy}
            >
              {copied ? "✓ Copied" : "Copy"}
            </button>
          )}
          {document.status === "completed" && (
            <button
              className="btn btn--secondary"
              onClick={handleResummarize}
              disabled={resummarizing}
            >
              {resummarizing ? "Re-summarizing…" : "Re-summarize"}
            </button>
          )}
        </div>
      </header>

      <div className="summary-viewer__content">
        {document.status === "processing" && (
          <div className="summary-viewer__loading">
            <div className="spinner" />
            <p>Analyzing and summarizing your document…</p>
            <p className="summary-viewer__loading-hint">
              This may take 10–30 seconds depending on document size.
            </p>
          </div>
        )}

        {document.status === "failed" && (
          <div className="summary-viewer__error">
            <p>⚠️ Summarization failed</p>
            {document.error_message && (
              <p className="summary-viewer__error-detail">
                {document.error_message}
              </p>
            )}
          </div>
        )}

        {document.status === "completed" && document.summary && (
          <div className="summary-viewer__text">
            {document.summary.split("\n").map((line, i) => {
              if (line.startsWith("# "))
                return <h1 key={i}>{line.slice(2)}</h1>;
              if (line.startsWith("## "))
                return <h2 key={i}>{line.slice(3)}</h2>;
              if (line.startsWith("### "))
                return <h3 key={i}>{line.slice(4)}</h3>;
              if (line.startsWith("- "))
                return (
                  <li key={i} className="summary-bullet">
                    {line.slice(2)}
                  </li>
                );
              if (line.startsWith("**") && line.endsWith("**"))
                return (
                  <p key={i}>
                    <strong>{line.slice(2, -2)}</strong>
                  </p>
                );
              if (line.trim() === "") return <br key={i} />;
              return <p key={i}>{line}</p>;
            })}
          </div>
        )}
      </div>
    </div>
  );
}
