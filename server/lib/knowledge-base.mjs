import { readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const knowledgeBasePath = path.resolve(__dirname, "../data/knowledge-base.json");

function tokenize(text = "") {
  return text
    .toLowerCase()
    .match(/[a-z0-9]+|[\u4e00-\u9fff]/g) ?? [];
}

function chunkText(text, chunkSize, overlap) {
  const normalized = String(text ?? "").replace(/\s+/g, " ").trim();
  if (!normalized) return [];
  const chunks = [];
  let cursor = 0;

  while (cursor < normalized.length) {
    const nextCursor = Math.min(normalized.length, cursor + chunkSize);
    chunks.push(normalized.slice(cursor, nextCursor));
    if (nextCursor >= normalized.length) break;
    cursor = Math.max(nextCursor - overlap, cursor + 1);
  }

  return chunks;
}

function scoreChunk(chunk, queryTokens) {
  if (!queryTokens.length) return 0;
  const chunkTokens = tokenize(chunk);
  if (!chunkTokens.length) return 0;

  const chunkSet = new Set(chunkTokens);
  let hitCount = 0;
  for (const token of queryTokens) {
    if (chunkSet.has(token)) {
      hitCount += 1;
    }
  }

  return hitCount / Math.sqrt(chunkSet.size);
}

export async function loadKnowledgeBase() {
  const raw = await readFile(knowledgeBasePath, "utf8");
  return JSON.parse(raw);
}

export async function saveKnowledgeBase(knowledgeBase) {
  await writeFile(knowledgeBasePath, JSON.stringify(knowledgeBase, null, 2), "utf8");
}

export async function addKnowledgeDocument(documentInput) {
  const knowledgeBase = await loadKnowledgeBase();
  const document = {
    id: `doc-${Date.now()}`,
    name: documentInput.name?.trim() || "未命名文档",
    category: documentInput.category?.trim() || "未分类",
    content: documentInput.content?.trim() || "",
    createdAt: new Date().toISOString()
  };

  knowledgeBase.documents.unshift(document);
  await saveKnowledgeBase(knowledgeBase);
  return document;
}

export async function removeKnowledgeDocument(documentId) {
  const knowledgeBase = await loadKnowledgeBase();
  const nextDocuments = knowledgeBase.documents.filter((item) => item.id !== documentId);
  const removed = nextDocuments.length !== knowledgeBase.documents.length;
  knowledgeBase.documents = nextDocuments;
  if (removed) {
    await saveKnowledgeBase(knowledgeBase);
  }
  return removed;
}

export async function retrieveKnowledgeContext(query, topK) {
  const knowledgeBase = await loadKnowledgeBase();
  const { chunkSize, chunkOverlap, retrievalTopK } = knowledgeBase.config;
  const queryTokens = tokenize(query);
  const chunks = knowledgeBase.documents.flatMap((document) =>
    chunkText(document.content, chunkSize, chunkOverlap).map((chunk, index) => ({
      id: `${document.id}#${index}`,
      documentId: document.id,
      documentName: document.name,
      category: document.category,
      content: chunk,
      score: scoreChunk(chunk, queryTokens)
    }))
  );

  return chunks
    .filter((item) => item.score > 0)
    .sort((left, right) => right.score - left.score)
    .slice(0, topK || retrievalTopK);
}
