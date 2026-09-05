import axios from "axios";
import { message } from "ant-design-vue";
import type {
  GeneratedResumeData,
  GeneratedResumeResponse,
  KnowledgeBaseConfig,
  KnowledgeBaseConfigUpdate,
  KnowledgeDocument,
  PromptTemplate,
  ResumeGenerateRequest
} from "../types/agent";
import { getAccessCode } from "../utils/accessCode";

/** 规范化的 API 错误:调用方只需读 code/message */
export class ApiError extends Error {
  code: number;
  constructor(code: number, messageText: string) {
    super(messageText);
    this.code = code;
    this.name = "ApiError";
  }
}

const FRIENDLY_STATUS_TEXT: Record<number, string> = {
  401: "访问口令缺失或不正确，请在「网站配置」页填写访问口令",
  403: "没有访问权限",
  404: "请求的资源不存在",
  413: "上传文件过大(上限 20MB)",
  429: "请求过于频繁，请稍后再试",
  500: "服务器内部错误，请稍后重试",
  502: "后端服务不可用或 LLM 未配置",
  504: "请求超时，请稍后重试",
};

const apiClient = axios.create({
  baseURL: "/api",
  timeout: 60000,
  headers: {
    "Content-Type": "application/json",
  },
});

// 请求拦截器:注入访问口令(后端 ACCESS_CODE 启用时必需)
apiClient.interceptors.request.use((config) => {
  const code = getAccessCode();
  if (code) {
    config.headers["X-Access-Code"] = code;
  }
  return config;
});

let authWarnedAt = 0;

// 响应拦截器:统一错误规范化 + 401 提示(避免每次弹重复消息)
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const status: number = error.response?.status ?? 0;
    const detail: string | undefined = error.response?.data?.detail;
    const friendly =
      detail ||
      FRIENDLY_STATUS_TEXT[status] ||
      (error.request ? "网络异常，请检查后端服务是否可用" : error.message);

    if (status === 401 && Date.now() - authWarnedAt > 3000) {
      authWarnedAt = Date.now();
      message.warning(FRIENDLY_STATUS_TEXT[401]);
    }
    return Promise.reject(new ApiError(status, friendly));
  }
);

export async function getBackendHealth() {
  const response = await apiClient.get("/health");
  return response.data as { ok: boolean; now: string; provider: string; embedding?: string; auth?: string };
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
