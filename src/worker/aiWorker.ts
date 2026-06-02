// AI Worker — forwards chat requests to local backend /api/chat proxy
self.onmessage = async (event) => {
  const { taskId, messages, userApiKey, model, API_URL } = event.data;

  const requestData = {
    api_url: API_URL,
    api_key: userApiKey,
    model: model,
    messages: messages,
    stream: true,
    temperature: 0.7,
  };

  try {
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestData),
    });

    if (response.status === 401) {
      self.postMessage({ taskId, isComplete: true, result: '认证失败，请检查 API Key 是否正确' });
      return;
    } else if (response.status === 400) {
      const errText = await response.text().catch(() => '未知错误');
      self.postMessage({ taskId, isComplete: true, result: `请求参数错误: ${errText}` });
      return;
    } else if (!response.ok) {
      const errText = await response.text().catch(() => `错误码: ${response.status}`);
      self.postMessage({ taskId, isComplete: true, result: `请求失败: ${errText}` });
      return;
    }

    if (!response.body) {
      self.postMessage({ taskId, isComplete: true, result: '服务器未返回流数据' });
      return;
    }

    // 读取流式响应数据（SSE）
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let currentText = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      const chunk = decoder.decode(value);
      const lines = chunk.split('\n').filter(line => line.trim() !== '');

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const jsonLine = line.slice(6).trim();  // 移除 `data: ` 前缀
          if (jsonLine === '[DONE]') {
            self.postMessage({ taskId, isComplete: true, result: currentText });
            return;
          }
          try {
            const parsedLine = JSON.parse(jsonLine);
            const deltaContent = parsedLine?.choices?.[0]?.delta?.content;
            if (deltaContent) {
              currentText += deltaContent;
              self.postMessage({ taskId, isComplete: false, result: currentText });
            }
          } catch (err) {
            self.postMessage({ taskId, result: '解析流数据时出错，请稍后重试' });
          }
        }
      }
    }

    // 流正常结束但没有 [DONE] 标志
    self.postMessage({ taskId, isComplete: true, result: currentText });
  } catch (error) {
    self.postMessage({ taskId, isComplete: true, result: '请求失败，请稍后重试' });
  }
};
