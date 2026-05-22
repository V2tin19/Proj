import http from "node:http";
import { readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import {
  addKnowledgeDocument,
  loadKnowledgeBase,
  removeKnowledgeDocument,
  retrieveKnowledgeContext
} from "./lib/knowledge-base.mjs";
import { generateResumePayload } from "./lib/resume-generator.mjs";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const promptTemplatesPath = path.resolve(__dirname, "./data/prompt-templates.json");
const port = Number(process.env.PORT || 3001);

async function loadPromptTemplates() {
  const raw = await readFile(promptTemplatesPath, "utf8");
  return JSON.parse(raw);
}

function setCorsHeaders(response) {
  response.setHeader("Access-Control-Allow-Origin", "*");
  response.setHeader("Access-Control-Allow-Methods", "GET,POST,DELETE,OPTIONS");
  response.setHeader("Access-Control-Allow-Headers", "Content-Type, Authorization");
}

function sendJson(response, statusCode, payload) {
  setCorsHeaders(response);
  response.writeHead(statusCode, { "Content-Type": "application/json; charset=utf-8" });
  response.end(JSON.stringify(payload));
}

function sendNotFound(response) {
  sendJson(response, 404, { message: "Not Found" });
}

async function readRequestBody(request) {
  const chunks = [];
  for await (const chunk of request) {
    chunks.push(chunk);
  }

  if (chunks.length === 0) {
    return {};
  }

  return JSON.parse(Buffer.concat(chunks).toString("utf8"));
}

function buildSearchQuery(input) {
  return [
    input.targetRole,
    input.applicationPosition,
    input.major,
    input.courses,
    input.skillsText,
    input.selfIntroduction
  ].filter(Boolean).join(" ");
}

const server = http.createServer(async (request, response) => {
  try {
    setCorsHeaders(response);

    if (!request.url) {
      sendNotFound(response);
      return;
    }

    const url = new URL(request.url, `http://${request.headers.host}`);
    const { pathname } = url;

    if (request.method === "OPTIONS") {
      response.writeHead(204);
      response.end();
      return;
    }

    if (request.method === "GET" && pathname === "/api/health") {
      sendJson(response, 200, {
        ok: true,
        now: new Date().toISOString(),
        provider: process.env.LLM_API_URL || process.env.OPENAI_COMPATIBLE_API_URL ? "llm-configured" : "local-fallback"
      });
      return;
    }

    if (request.method === "GET" && pathname === "/api/prompt-templates") {
      const templates = await loadPromptTemplates();
      sendJson(response, 200, templates);
      return;
    }

    if (request.method === "GET" && pathname === "/api/knowledge-base/config") {
      const knowledgeBase = await loadKnowledgeBase();
      sendJson(response, 200, knowledgeBase.config);
      return;
    }

    if (request.method === "GET" && pathname === "/api/knowledge-base/documents") {
      const knowledgeBase = await loadKnowledgeBase();
      sendJson(response, 200, knowledgeBase.documents);
      return;
    }

    if (request.method === "POST" && pathname === "/api/knowledge-base/documents") {
      const body = await readRequestBody(request);
      if (!body?.name || !body?.content) {
        sendJson(response, 400, { message: "name and content are required" });
        return;
      }

      const document = await addKnowledgeDocument(body);
      sendJson(response, 201, document);
      return;
    }

    if (request.method === "DELETE" && pathname.startsWith("/api/knowledge-base/documents/")) {
      const documentId = pathname.split("/").pop();
      const removed = documentId ? await removeKnowledgeDocument(documentId) : false;
      sendJson(response, removed ? 200 : 404, { removed });
      return;
    }

    if (request.method === "POST" && pathname === "/api/generate-resume") {
      const body = await readRequestBody(request);
      const templates = await loadPromptTemplates();
      const template = templates.find((item) => item.id === body.templateId) || templates[0];
      const searchQuery = buildSearchQuery(body);
      const knowledgeHits = body.enableRag === false ? [] : await retrieveKnowledgeContext(searchQuery, body.retrievalTopK);
      const result = await generateResumePayload(body, template, knowledgeHits);
      sendJson(response, 200, result);
      return;
    }

    sendNotFound(response);
  } catch (error) {
    console.error(error);
    sendJson(response, 500, {
      message: "Internal Server Error",
      error: error instanceof Error ? error.message : "unknown"
    });
  }
});

server.listen(port, () => {
  console.log(`AIResume backend server listening on http://localhost:${port}`);
});
