/**
 * Chat API client — Q&A over documents.
 */

import { apiPost } from "./client";

export interface ChatRequest {
  query: string;
  document_id: number;
}

export interface ChatResponse {
  answer: string;
  context_chunks: string[];
  tokens_used: number;
  provider: string;
}

export async function chatWithDocument(
  request: ChatRequest,
  signal?: AbortSignal,
): Promise<ChatResponse> {
  return apiPost<ChatResponse>("/api/chat", request, signal);
}
