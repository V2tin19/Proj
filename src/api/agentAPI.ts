import axios from "axios";
import type {
  GeneratedResumeData,
  GeneratedResumeResponse,
  KnowledgeBaseConfig,
  KnowledgeBaseConfigUpdate,
  KnowledgeDocument,
  PromptTemplate,
  ResumeGenerateRequest
} from "../types/agent";

const apiClient = axios.create({
  baseURL: "/api",
  timeout: 60000,
  headers: {
    "Content-Type": "application/json",
  },
});

// 响应拦截器：统一错误处理
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      console.error("API Error:", error.response.status, error.response.data);
    } else if (error.request) {
      console.error("API No Response:", error.request);
    } else {
      console.error("API Request Error:", error.message);
    }
    return Promise.reject(error);
  }
);

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

export async function exportResumeDocx(payload: GeneratedResumeData) {
  const response = await apiClient.post("/export-resume/docx", payload, {
    responseType: "blob",
  });
  return response.data as Blob;
}

export async function updateKnowledgeBaseConfig(payload: KnowledgeBaseConfigUpdate) {
  const response = await apiClient.put("/knowledge-base/config", payload);
  return response.data as KnowledgeBaseConfig;
}

export async function uploadKnowledgeDocument(file: File) {
  const formData = new FormData();
  formData.append("file", file);
  const response = await apiClient.post("/knowledge-base/documents/upload", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
  return response.data as KnowledgeDocument;
}
