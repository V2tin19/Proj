// AI Worker — 转发对话请求到后端 /api/chat(SSE 流式代理)。
// 协议:事件以空行分隔;同一事件内的多行 data 用 \n 还原(换行不丢失);
// 终止符 data: [DONE];任何网络/超时错误都以 error 标记回报,绝不悬挂 UI。
import { getAccessCode } from "../utils/accessCode";

const REQUEST_TIMEOUT_MS = 125_000; // 后端 chat 上游超时 120s,留 5s 余量

interface WorkerIncoming {
  taskId: number;
  messages: Array<{ role: string; content: string }>;
}

self.onmessage = async (event: MessageEvent<WorkerIncoming>) => {
  const { taskId, messages } = event.data;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  const fail = (message: string) => {
    self.postMessage({ taskId, isComplete: true, error: true, result: message });
  };

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Access-Code": getAccessCode(),
      },
      body: JSON.stringify({ messages, stream: true }),
      signal: controller.signal,
    });

    if (response.status === 401) {
      fail("访问口令缺失或不正确，请在「网站配置」页填写访问口令");
      return;
    }
    if (response.status === 400) {
      const errText = await response.text().catch(() => "未知错误");
      fail(`请求参数错误: ${errText.slice(0, 200)}`);
      return;
    }
    if (!response.ok) {
      const errText = await response.text().catch(() => `错误码: ${response.status}`);
      fail(`请求失败: ${errText.slice(0, 200)}`);
      return;
    }
    if (!response.body) {
      fail("服务器未返回流数据");
      return;
    }

    // SSE 解析:按事件(空行分隔)聚合 data 行,事件内多行用 \n 还原,
    // 修复多行回复换行丢失的问题。
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let currentText = "";
    let buffer = "";
    let dataLines: string[] = [];

    const finishEvent = (): boolean => {
      const data = dataLines.join("\n");
      dataLines = [];
      if (!data) return false;
      if (data === "[DONE]") return true;
      currentText += data;
      self.postMessage({ taskId, isComplete: false, result: currentText });
      return false;
    };

    let done = false;
    while (!done) {
      const read = await reader.read();
      done = read.done;
      buffer += decoder.decode(read.value ?? new Uint8Array(), { stream: true });

      const lines = buffer.split("\n");
      buffer = lines.pop() || "";

      for (const rawLine of lines) {
        const line = rawLine.trimEnd();
        if (line === "") {
          if (finishEvent()) {
            self.postMessage({ taskId, isComplete: true, result: currentText });
            clearTimeout(timer);
            return;
          }
          continue;
        }
        if (line.startsWith("data:")) {
          dataLines.push(line.slice(5).replace(/^ /, ""));
        }
      }
    }
    // 流收尾:处理未换行的残余事件
    if (buffer.trimStart().startsWith("data:")) {
      dataLines.push(buffer.trimStart().slice(5).replace(/^ /, ""));
    }
    finishEvent();
    self.postMessage({ taskId, isComplete: true, result: currentText });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      fail("请求超时，请稍后重试");
    } else {
      fail("网络异常，请检查后端服务是否可用");
    }
  } finally {
    clearTimeout(timer);
  }
};
