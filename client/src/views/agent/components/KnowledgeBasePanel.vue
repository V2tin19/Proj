<template>
  <div>
    <div class="form-section">
      <div class="section-title">
        <span>知识库配置</span>
        <div>
          <a-button size="small" @click="loadResources" style="margin-right: 8px;">刷新</a-button>
          <a-button size="small" type="primary" :loading="savingConfig" @click="saveConfig">保存配置</a-button>
        </div>
      </div>
      <div v-if="config" class="config-grid">
        <div class="config-item">
          <span>分块大小</span>
          <a-input-number v-model:value="configForm.chunkSize" :min="50" :max="2000" style="width: 100%;" />
        </div>
        <div class="config-item">
          <span>分块重叠</span>
          <a-input-number v-model:value="configForm.chunkOverlap" :min="0" :max="500" style="width: 100%;" />
        </div>
        <div class="config-item">
          <span>Top K</span>
          <a-input-number v-model:value="configForm.retrievalTopK" :min="1" :max="100" style="width: 100%;" />
        </div>
        <div class="config-item">
          <span>匹配算法</span>
          <a-select v-model:value="configForm.matchAlgorithm" style="width: 100%;">
            <a-select-option value="token-overlap">token-overlap</a-select-option>
            <a-select-option value="vector-cosine">vector-cosine</a-select-option>
          </a-select>
        </div>
        <div class="config-item">
          <span>向量/检索实现</span>
          <a-select v-model:value="configForm.embeddingProvider" style="width: 100%;">
            <a-select-option value="local">local</a-select-option>
          </a-select>
        </div>
      </div>
    </div>

    <div class="form-section">
      <div class="section-title">
        <span>新增知识条目</span>
      </div>
      <a-tabs size="small">
        <a-tab-pane key="text" tab="手动录入">
          <div class="grid-two">
            <a-input v-model:value="documentForm.name" placeholder="文档名称" />
            <a-input v-model:value="documentForm.category" placeholder="分类，如技术岗 / 写作规范" />
          </div>
          <a-textarea
            v-model:value="documentForm.content"
            :auto-size="{ minRows: 5, maxRows: 8 }"
            placeholder="粘贴简历模板规范、岗位描述经验、优秀案例要点等文本内容"
          />
          <a-button type="primary" :loading="savingDocument" @click="submitDocument">
            保存到知识库
          </a-button>
        </a-tab-pane>
        <a-tab-pane key="upload" tab="文件上传">
          <a-upload-dragger
            :showUploadList="false"
            :beforeUpload="handleFileUpload"
            :disabled="uploading"
            accept=".docx,.pdf,.txt,.md"
          >
            <p class="ant-upload-drag-icon">
              <upload-outlined />
            </p>
            <p class="ant-upload-text">点击或拖拽文件到此区域上传</p>
            <p class="ant-upload-hint">支持 .docx、.pdf、.txt、.md，单文件不超过 20MB</p>
          </a-upload-dragger>
        </a-tab-pane>
      </a-tabs>
    </div>

    <div class="form-section">
      <div class="section-title">
        <span>已有知识条目</span>
      </div>
      <a-empty v-if="documents.length === 0" description="暂时还没有知识条目" />
      <div v-else class="knowledge-list">
        <div v-for="item in documents" :key="item.id" class="knowledge-card">
          <div class="knowledge-top">
            <div>
              <strong>{{ item.name }}</strong>
              <p>{{ item.category }}</p>
            </div>
            <a-popconfirm
              title="确定删除这个知识条目吗？"
              ok-text="删除"
              cancel-text="取消"
              @confirm="removeDocument(item.id)"
            >
              <a-button size="small" danger ghost>删除</a-button>
            </a-popconfirm>
          </div>
          <p class="knowledge-content">{{ item.content }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";
import { message } from "ant-design-vue";
import { UploadOutlined } from "@ant-design/icons-vue";
import {
  createKnowledgeDocument,
  deleteKnowledgeDocument,
  getKnowledgeBaseConfig,
  getKnowledgeDocuments,
  updateKnowledgeBaseConfig,
  uploadKnowledgeDocument,
  type ApiError,
} from "../../../api/agentAPI";
import type {
  KnowledgeBaseConfig,
  KnowledgeDocument,
} from "../../../types/agent";

const MAX_UPLOAD_BYTES = 20 * 1024 * 1024;
const ALLOWED_EXTENSIONS = [".docx", ".pdf", ".txt", ".md"];

const config = ref<KnowledgeBaseConfig | null>(null);
const documents = ref<KnowledgeDocument[]>([]);
const savingConfig = ref(false);
const configForm = reactive<KnowledgeBaseConfig>({
  chunkSize: 300,
  chunkOverlap: 50,
  retrievalTopK: 5,
  matchAlgorithm: "token-overlap",
  embeddingProvider: "local",
});

const documentForm = reactive({ name: "", category: "", content: "" });
const savingDocument = ref(false);
const uploading = ref(false);

async function loadResources() {
  const [loadedConfig, loadedDocuments] = await Promise.all([
    getKnowledgeBaseConfig(),
    getKnowledgeDocuments(),
  ]);
  config.value = loadedConfig;
  documents.value = loadedDocuments;
  if (loadedConfig) {
    configForm.chunkSize = loadedConfig.chunkSize;
    configForm.chunkOverlap = loadedConfig.chunkOverlap;
    configForm.retrievalTopK = loadedConfig.retrievalTopK;
    configForm.matchAlgorithm = loadedConfig.matchAlgorithm;
    configForm.embeddingProvider = loadedConfig.embeddingProvider;
  }
}

async function saveConfig() {
  savingConfig.value = true;
  try {
    const updated = await updateKnowledgeBaseConfig({ ...configForm });
    config.value = updated;
    message.success("知识库配置已保存");
  } catch (error) {
    console.error(error);
    message.error((error as ApiError).message || "保存知识库配置失败");
  } finally {
    savingConfig.value = false;
  }
}

async function submitDocument() {
  if (!documentForm.name.trim() || !documentForm.content.trim()) {
    message.warning("请先填写文档名称和内容");
    return;
  }
  savingDocument.value = true;
  try {
    await createKnowledgeDocument({
      name: documentForm.name,
      category: documentForm.category || "未分类",
      content: documentForm.content,
    });
    documentForm.name = "";
    documentForm.category = "";
    documentForm.content = "";
    await loadResources();
    message.success("知识条目已写入本地知识库");
  } catch (error) {
    console.error(error);
    message.error((error as ApiError).message || "保存知识条目失败");
  } finally {
    savingDocument.value = false;
  }
}

async function removeDocument(documentId: string) {
  try {
    await deleteKnowledgeDocument(documentId);
    documents.value = documents.value.filter((item) => item.id !== documentId);
    message.success("知识条目已删除");
  } catch (error) {
    console.error(error);
    message.error((error as ApiError).message || "删除知识条目失败");
  }
}

async function handleFileUpload(file: File) {
  const ext = file.name.slice(file.name.lastIndexOf(".")).toLowerCase();
  if (!ALLOWED_EXTENSIONS.includes(ext)) {
    message.error("仅支持 .docx、.pdf、.txt、.md 格式");
    return false;
  }
  if (file.size > MAX_UPLOAD_BYTES) {
    message.error("文件大小不能超过 20MB");
    return false;
  }
  uploading.value = true;
  try {
    await uploadKnowledgeDocument(file);
    await loadResources();
    message.success(`文件 "${file.name}" 已解析并入库`);
  } catch (error) {
    console.error(error);
    message.error((error as ApiError).message || "文件上传失败");
  } finally {
    uploading.value = false;
  }
  return false;
}

onMounted(loadResources);

defineExpose({ refresh: loadResources });
</script>

<style scoped>
.form-section {
  margin-bottom: 20px;
  padding: 18px;
  border-radius: 16px;
  background: rgba(11, 18, 29, 0.82);
  border: 1px solid rgba(80, 100, 140, 0.18);
}

.section-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
  color: var(--text-color);
  font-weight: 600;
}

.grid-two {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.form-section :deep(.ant-input),
.form-section :deep(.ant-select),
.form-section :deep(.ant-input-affix-wrapper),
.form-section :deep(.ant-input-number),
.form-section :deep(.ant-input-textarea) {
  margin-bottom: 12px;
}

.config-grid {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.config-item {
  padding: 14px;
  border-radius: 14px;
  background: rgba(15, 23, 36, 0.9);
  border: 1px solid rgba(80, 100, 140, 0.18);
}

.config-item span {
  display: block;
  margin-bottom: 8px;
  color: var(--text-muted);
  font-size: 12px;
}

.knowledge-card {
  padding: 16px;
  border-radius: 14px;
  border: 1px solid rgba(80, 100, 140, 0.18);
  background: rgba(15, 23, 36, 0.9);
}

.knowledge-card + .knowledge-card {
  margin-top: 14px;
}

.knowledge-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.knowledge-top strong {
  margin: 0;
  color: var(--text-color);
}

.knowledge-top p {
  margin: 8px 0 0;
  display: block;
  color: var(--text-muted);
  line-height: 1.6;
}

.knowledge-content {
  white-space: pre-wrap;
  line-height: 1.7;
  color: var(--text-muted);
}
</style>
