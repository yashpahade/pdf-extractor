import { useCallback, useState } from "react";
import { uploadDocument, type DocumentMeta } from "../api/documents";

const ACCEPTED_TYPES = [
  "application/pdf",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  "image/png",
  "image/jpeg",
  "image/webp",
];

const MAX_SIZE = 20 * 1024 * 1024; // 20 MB

interface Props {
  onUploaded: (doc: DocumentMeta) => void;
}

export default function UploadZone({ onUploaded }: Props) {
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFile = useCallback(
    async (file: File) => {
      setError(null);

      if (!ACCEPTED_TYPES.includes(file.type)) {
        setError(
          "Unsupported file type. Use PDF, DOCX, PNG, JPG, or WEBP.",
        );
        return;
      }
      if (file.size > MAX_SIZE) {
        setError("File too large. Maximum size is 20 MB.");
        return;
      }

      setUploading(true);
      try {
        const doc = await uploadDocument(file);
        onUploaded(doc);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Upload failed",
        );
      } finally {
        setUploading(false);
      }
    },
    [onUploaded],
  );

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragging(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile],
  );

  const onFileInput = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) handleFile(file);
      e.target.value = "";
    },
    [handleFile],
  );

  return (
    <div
      className={`upload-zone ${dragging ? "upload-zone--active" : ""} ${uploading ? "upload-zone--uploading" : ""}`}
      onDragOver={(e) => {
        e.preventDefault();
        setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={onDrop}
    >
      <div className="upload-zone__content">
        <div className="upload-zone__icon">📄</div>
        {uploading ? (
          <p className="upload-zone__text">Processing document…</p>
        ) : (
          <>
            <p className="upload-zone__text">
              Drag & drop a file here, or{" "}
              <label className="upload-zone__link">
                browse
                <input
                  type="file"
                  accept=".pdf,.docx,.png,.jpg,.jpeg,.webp"
                  onChange={onFileInput}
                  hidden
                />
              </label>
            </p>
            <p className="upload-zone__hint">
              PDF, DOCX, PNG, JPG, WEBP — max 20 MB
            </p>
          </>
        )}
        {error && <p className="upload-zone__error">{error}</p>}
      </div>
    </div>
  );
}
