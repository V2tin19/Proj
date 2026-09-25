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
import { clearSession, getServerBase, getToken, getSessionUser } from "../utils/auth";

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
  401: "未登录或登录已过期，请重新登录",
  403: "没有访问权限",
  404: "请求的资源不存在",
  409: "用户名已被注册",
  413: "上传文件过大(上限 20MB)",
  422: "输入格式不符合要求",
  429: "请求过于频繁，请稍后再试",
  500: "服务器内部错误，请稍后重试",
  502: "后端服务不可用或 LLM 未配置",
  504: "请求超时，请稍后重试",
};

const apiClient = axios.create({
  timeout: 60000,
  headers: {
    "Content-Type": "application/json",
  },
});

// 请求拦截器:服务端地址(C/S 可配置,留空=同源)+ Bearer 令牌
apiClient.interceptors.request.use((config) => {
  config.baseURL = `${getServerBase()}/api`;
  const token = getToken();
  if (token) {
    config.headers["Authorization"] = `Bearer ${token}`;
  }
  return config;
});

let authBounced = false;

// 响应拦截器:统一错误规范化;登录态失效(401)清会话并跳转登录页
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const status: number = error.response?.status ?? 0;
    const detail: string | undefined = error.response?.data?.detail;
    const friendly =
      detail ||
      FRIENDLY_STATUS_TEXT[status] ||
      (error.request ? "网络异常，请检查服务端地址与网络" : error.message);

    if (status === 401 && getToken() && !authBounced) {
      authBounced = true;
      clearSession();
      message.warning(FRIENDLY_STATUS_TEXT[401]);
      try {
        const { default: router } = await import("../router");
        await router.push({ name: "auth" });
      } finally {
        setTimeout(() => (authBounced = false), 1000);
      }
    }
    return Promise.reject(new ApiError(status, friendly));
  }
);

// ------------------------------------------------------------------ 账号

export interface SessionPayload {
  token: string;
  expiresAt: string;
  username: string;
  role: "user" | "admin";
}

export async function registerAccount(payload: { username: string; password: string; email?: string; inviteCode?: string }) {
  const response = await apiClient.post("/auth/register", payload);
  return response.data as SessionPayload;
}

export async function loginAccount(payload: { username: string; password: string }) {
  const response = await apiClient.post("/auth/login", payload);
  return response.data as SessionPayload;
}

export async function logoutAccount() {
  try {
    await apiClient.post("/auth/logout");
  } finally {
    clearSession();
  }
}

export async function fetchMe() {
  const response = await apiClient.get("/auth/me");
  return response.data as { username: string; role: "user" | "admin"; email: string };
}

// ------------------------------------------------------------------ 业务

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

// 供 Worker 组装请求使用(工作线程无法读 localStorage)
export function getWorkerAuthContext() {
  return { serverBase: getServerBase(), token: getToken(), user: getSessionUser() };
}
