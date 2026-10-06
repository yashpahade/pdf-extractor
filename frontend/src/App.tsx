import { useEffect, useState, useCallback } from "react";
import {
  listDocuments,
  getDocument,
  deleteDocument,
  type DocumentMeta,
} from "./api/documents";
import Layout from "./components/Layout";
import UploadZone from "./components/UploadZone";
import DocumentList from "./components/DocumentList";
import SummaryViewer from "./components/SummaryViewer";
import ChatPanel from "./components/ChatPanel";
import "./app.css";

export default function App() {
  const [documents, setDocuments] = useState<DocumentMeta[]>([]);
  const [selectedDoc, setSelectedDoc] = useState<DocumentMeta | null>(null);

  const refreshDocuments = useCallback(async () => {
    try {
      const { documents: docs } = await listDocuments();
      setDocuments(docs);
    } catch {
      // silent — health check may fail on first load
    }
  }, []);

  // Initial load
  useEffect(() => {
    refreshDocuments();
  }, [refreshDocuments]);

  // Poll for processing documents
  useEffect(() => {
    const processing = documents.some(
      (d) => d.status === "processing" || d.status === "uploading",
    );
    if (!processing) return;

    const interval = setInterval(async () => {
      await refreshDocuments();

      // Also refresh selected doc if it's processing
      if (
        selectedDoc &&
        (selectedDoc.status === "processing" ||
          selectedDoc.status === "uploading")
      ) {
        try {
          const updated = await getDocument(selectedDoc.id);
          setSelectedDoc(updated);
        } catch {
          // ignore
        }
      }
    }, 3000);

    return () => clearInterval(interval);
  }, [documents, selectedDoc, refreshDocuments]);

  const handleUploaded = useCallback(
    (doc: DocumentMeta) => {
      setDocuments((prev) => [doc, ...prev]);
      setSelectedDoc(doc);
    },
    [],
  );

  const handleSelect = useCallback((doc: DocumentMeta) => {
    setSelectedDoc(doc);
  }, []);

  const handleDelete = useCallback(
    async (id: number) => {
      try {
        await deleteDocument(id);
        setDocuments((prev) => prev.filter((d) => d.id !== id));
        if (selectedDoc?.id === id) setSelectedDoc(null);
      } catch {
        // ignore
      }
    },
    [selectedDoc],
  );

  const handleDocumentUpdated = useCallback(
    (updated: DocumentMeta) => {
      setDocuments((prev) =>
        prev.map((d) => (d.id === updated.id ? updated : d)),
      );
      if (selectedDoc?.id === updated.id) setSelectedDoc(updated);
    },
    [selectedDoc],
  );

  return (
    <Layout
      sidebar={
        <>
          <UploadZone onUploaded={handleUploaded} />
          <DocumentList
            documents={documents}
            selectedId={selectedDoc?.id ?? null}
            onSelect={handleSelect}
            onDelete={handleDelete}
          />
        </>
      }
      main={
        <SummaryViewer
          document={selectedDoc}
          onDocumentUpdated={handleDocumentUpdated}
        />
      }
      chat={<ChatPanel documentId={selectedDoc?.id ?? null} />}
    />
  );
}
