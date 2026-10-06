/**
 * Document API client — upload, list, get, delete documents.
 */

import { apiGet, apiPost, apiDelete } from "./client";

export interface DocumentMeta {
  id: number;
  filename: string;
  media_type: string;
  file_size_bytes: number;
  status: "uploading" | "processing" | "completed" | "failed";
  page_count: number | null;
  summary: string | null;
  error_message: string | null;
  tokens_used: number;
  provider_used: string | null;
  processing_time_ms: number | null;
  created_at: string;
}

export interface DocumentListResponse {
  documents: DocumentMeta[];
  total: number;
}

export async function uploadDocument(
  file: File,
  signal?: AbortSignal,
): Promise<DocumentMeta> {
  const form = new FormData();
  form.append("file", file);
  return apiPost<DocumentMeta>("/api/documents/upload", form, signal);
}

export async function listDocuments(
  signal?: AbortSignal,
): Promise<DocumentListResponse> {
  return apiGet<DocumentListResponse>("/api/documents", signal);
}

export async function getDocument(
  id: number,
  signal?: AbortSignal,
): Promise<DocumentMeta> {
  return apiGet<DocumentMeta>(`/api/documents/${id}`, signal);
}

export async function deleteDocument(id: number): Promise<void> {
  return apiDelete(`/api/documents/${id}`);
}

export async function resummarize(
  id: number,
  instruction?: string,
): Promise<DocumentMeta> {
  return apiPost<DocumentMeta>(`/api/documents/${id}/resummarize`, {
    instruction,
  });
}
