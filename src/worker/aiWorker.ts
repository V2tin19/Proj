// AI Worker — forwards chat requests to local backend /api/chat proxy
// Backend now manages credentials, model selection, and SSE protocol parsing.
self.onmessage = async (event) => {
  const { taskId, messages } = event.data;

  const requestData = {
    messages: messages,
    stream: true,
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
      self.postMessage({ taskId, isComplete: true, result: '认证失败，请检查后端 API Key 配置' });
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

    // Backend returns simplified SSE: each non-empty line is already a delta text.
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let currentText = '';
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const rawLine of lines) {
        const line = rawLine.trim();
        if (!line) continue;
        if (!line.startsWith('data: ')) continue;

        const data = line.slice(6).trim();
        if (data === '[DONE]') {
          self.postMessage({ taskId, isComplete: true, result: currentText });
          return;
        }

        currentText += data;
        self.postMessage({ taskId, isComplete: false, result: currentText });
      }
    }

    // Flush remaining buffer
    const line = buffer.trim();
    if (line.startsWith('data: ')) {
      const data = line.slice(6).trim();
      if (data !== '[DONE]') {
        currentText += data;
      }
    }

    // Stream ended normally
    self.postMessage({ taskId, isComplete: true, result: currentText });
  } catch (error) {
    self.postMessage({ taskId, isComplete: true, result: '请求失败，请稍后重试' });
  }
};
