import { type DocumentMeta } from "../api/documents";

const STATUS_LABELS: Record<string, { label: string; className: string }> = {
  uploading: { label: "Uploading", className: "badge badge--info" },
  processing: { label: "Processing", className: "badge badge--warning" },
  completed: { label: "Completed", className: "badge badge--success" },
  failed: { label: "Failed", className: "badge badge--error" },
};

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function fileIcon(mediaType: string): string {
  if (mediaType.includes("pdf")) return "📕";
  if (mediaType.includes("word") || mediaType.includes("docx")) return "📘";
  if (mediaType.startsWith("image/")) return "🖼️";
  return "📄";
}

interface Props {
  documents: DocumentMeta[];
  selectedId: number | null;
  onSelect: (doc: DocumentMeta) => void;
  onDelete: (id: number) => void;
}

export default function DocumentList({
  documents,
  selectedId,
  onSelect,
  onDelete,
}: Props) {
  if (documents.length === 0) {
    return (
      <div className="doc-list__empty">
        <p>No documents yet</p>
        <p className="doc-list__empty-hint">Upload a file to get started</p>
      </div>
    );
  }

  return (
    <ul className="doc-list">
      {documents.map((doc) => {
        const status = STATUS_LABELS[doc.status] ?? STATUS_LABELS.processing;
        return (
          <li
            key={doc.id}
            className={`doc-list__item ${
              doc.id === selectedId ? "doc-list__item--selected" : ""
            }`}
            onClick={() => onSelect(doc)}
          >
            <div className="doc-list__item-header">
              <span className="doc-list__icon">{fileIcon(doc.media_type)}</span>
              <span className="doc-list__name" title={doc.filename}>
                {doc.filename}
              </span>
              <button
                className="doc-list__delete"
                title="Delete"
                onClick={(e) => {
                  e.stopPropagation();
                  onDelete(doc.id);
                }}
              >
                ✕
              </button>
            </div>
            <div className="doc-list__item-meta">
              <span className={status.className}>{status.label}</span>
              <span className="doc-list__size">
                {formatBytes(doc.file_size_bytes)}
              </span>
              {doc.tokens_used > 0 && (
                <span className="doc-list__tokens">
                  {doc.tokens_used.toLocaleString()} tokens
                </span>
              )}
            </div>
          </li>
        );
      })}
    </ul>
  );
}
