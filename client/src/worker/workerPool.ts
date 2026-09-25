import type { DialogueHistory } from "../types/aiDialogue";

export interface WorkerAuthContext {
  serverBase: string;
  token: string;
}

interface QueueTask {
  taskId: number;
  messages: DialogueHistory;
  auth: WorkerAuthContext;
  onResponse: (responseText: string, isComplete: boolean, error?: boolean) => void;
}

export class WorkerPool {
  private workers: Worker[] = []; // 空闲 Worker 线程
  private queue: QueueTask[] = []; // 任务队列
  private activeTasks = 0; // 正在执行的任务数
  private nextTaskId = 1; // 任务 ID 计数器

  constructor(workerCount: number) {
    for (let i = 0; i < workerCount; i++) {
      const worker = new Worker(new URL("./aiWorker.ts", import.meta.url), { type: "module" });
      worker.onerror = (error) => {
        console.error("Worker 异常:", error);
        this.workers.push(worker);
        this.processQueue();
      };
      this.workers.push(worker);
    }
  }

  /**
   * 新增任务
   * @param messages  对话历史
   * @param onResponse  结果回调(isComplete=true 时结束;error=true 表示失败)
   */
  execute(
    messages: DialogueHistory,
    onResponse: (responseText: string, isComplete: boolean, error?: boolean) => void,
    auth: WorkerAuthContext = { serverBase: "", token: "" }
  ): void {
    const taskId = this.nextTaskId++;
    this.queue.push({ taskId, messages, auth, onResponse });
    this.processQueue();
  }

  private processQueue() {
    if (this.queue.length === 0 || this.workers.length === 0) return;
    const worker = this.workers.pop()!;
    const { taskId, messages, auth, onResponse } = this.queue.shift()!;
    this.activeTasks++;
    try {
      // postMessage 用结构化克隆;显式克隆一份防止调用方继续修改
      const clonedMessages = JSON.parse(JSON.stringify(messages));
      worker.onmessage = (event: MessageEvent) => {
        const { result, isComplete, error } = event.data;
        onResponse(result, isComplete, error);
        if (isComplete) {
          this.activeTasks--;
          this.workers.push(worker);
          this.processQueue();
        }
      };
      worker.postMessage({ taskId, messages: clonedMessages, ...auth });
    } catch (error) {
      this.activeTasks--;
      onResponse("数据传输失败", true, true);
      this.workers.push(worker);
      this.processQueue();
    }
  }

  /** 终止所有 Worker */
  terminate() {
    this.workers.forEach((worker) => worker.terminate());
    this.workers = [];
    this.queue = [];
    this.activeTasks = 0;
  }
}
