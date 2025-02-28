import { useSettingsStore } from "../store/useSettingsStore";
import { message } from "ant-design-vue";
import type { DialogueHistory } from "../types/aiDialogue";
//读取用户设置的API地址和API Key
const settingsStore = useSettingsStore();
const API_URL = settingsStore.aliApiUrl;
const userApiKey = settingsStore.aliApiKey;
const model = settingsStore.modelName;

// 多轮AI对话
export async function sendToQwenAIDialogue(messages: DialogueHistory,
  onResponse: (responseText: string, isComplete: boolean) => void): Promise<void> {

  const requestData = {
    model: model,
    messages: messages,
    stream: true,
    stream_options: {
      include_usage: true
    }
  };
  try {
    const response = await fetch(API_URL, {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${userApiKey}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(requestData),
    });

    // 返回情况检查
    if (response.status === 401) {
      onResponse("认证失败，请检查 API Key 是否正确", true);
      message.error("认证失败，请检查 API Key 是否正确");
      return;
    } else if (!response.ok) {
      onResponse(`请求失败，错误码: ${response.status}`, true);
      message.error(`请求失败，错误码: ${response.status}`);
      return;
    }
    if (!response.body) {
      onResponse("服务器未返回流数据", true);
      throw new Error("服务器未返回流数据");

    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let currentText = "";
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value);
      const lines = chunk.split('\n').filter(line => line.trim() !== '');

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const jsonLine = line.slice(6).trim();
          if (jsonLine === '[DONE]') {
            onResponse(currentText, true);
            return;
          }
          try {
            const parsedLine = JSON.parse(jsonLine);
            if (Array.isArray(parsedLine.choices) && parsedLine.choices.length === 0) {
              continue;
            }
            const deltaContent = parsedLine?.choices?.[0]?.delta?.content;
            if (deltaContent) {
              currentText += deltaContent;
              onResponse(currentText, false);
            }
          } catch (err) {
            onResponse("解析流数据时出错，请稍后重试", true);
            console.error("解析流数据时出错:", err);
          }
        }
      }
    }
  } catch (error) {
    console.error("请求 Qwen AI 失败:", error);
    message.error("请求失败，请稍后重试");
    onResponse("请求失败，请稍后重试", true);
  }
}
