import axios from "axios";
import type {
  GeneratedResumeResponse,
  KnowledgeBaseConfig,
  KnowledgeDocument,
  PromptTemplate,
  ResumeGenerateRequest
} from "../types/agent";

const apiClient = axios.create({
  baseURL: "/api",
  timeout: 60000
});

export async function getBackendHealth() {
  const response = await apiClient.get("/health");
  return response.data as { ok: boolean; now: string; provider: string };
}

export async function getPromptTemplates() {
  const response = await apiClient.get("/prompt-templates");
  return response.data as PromptTemplate[];
}

export async function getKnowledgeBaseConfig() {
  const response = await apiClient.get("/knowledge-base/config");
  return response.data as KnowledgeBaseConfig;
}

export async function getKnowledgeDocuments() {
  const response = await apiClient.get("/knowledge-base/documents");
  return response.data as KnowledgeDocument[];
}

export async function createKnowledgeDocument(payload: Pick<KnowledgeDocument, "name" | "category" | "content">) {
  const response = await apiClient.post("/knowledge-base/documents", payload);
  return response.data as KnowledgeDocument;
}

export async function deleteKnowledgeDocument(documentId: string) {
  const response = await apiClient.delete(`/knowledge-base/documents/${documentId}`);
  return response.data as { removed: boolean };
}

export async function generateResume(payload: ResumeGenerateRequest) {
  const response = await apiClient.post("/generate-resume", payload);
  return response.data as GeneratedResumeResponse;
}
