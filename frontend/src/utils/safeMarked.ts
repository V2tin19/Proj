import DOMPurify from "dompurify";
import { marked } from "marked";

/**
 * Markdown → 安全 HTML。
 * 所有 AI 返回内容必须经过本函数再进 v-html,防止 prompt injection / XSS。
 */
export function safeMarked(input: string | null | undefined): string {
  if (!input) return "";
  const rawHtml = marked.parse(String(input), { async: false }) as string;
  return DOMPurify.sanitize(rawHtml, {
    FORBID_TAGS: ["style", "form", "input", "button", "iframe"],
    FORBID_ATTR: ["onerror", "onclick", "onload", "style"],
  });
}
