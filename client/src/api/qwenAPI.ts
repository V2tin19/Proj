import type { DialogueHistory } from "../types/aiDialogue";
import { WorkerPool } from "../worker/workerPool";
import { getWorkerAuthContext } from "./agentAPI";

// 创建线程池，最多 4 个工作线程
const workerPool = new WorkerPool(4);

export async function sendToQwenAIDialogue(
  messages: DialogueHistory,
  onResponse: (responseText: string, isComplete: boolean) => void
): Promise<void> {
  workerPool.execute(messages, onResponse, getWorkerAuthContext());
}
