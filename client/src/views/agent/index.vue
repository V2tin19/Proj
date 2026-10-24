<template>
  <div class="agent-page">
    <div class="workspace">
      <section class="left-panel">
        <div class="panel-header">
          <div>
            <h1>简历智能体</h1>
            <p>以当前简历档案为数据源，配置生成策略后一键生成结构化简历。</p>
          </div>
          <div class="status-box">
            <span class="status-label">后端状态</span>
            <a-tag class="status-tag" :color="backendStatusColor">{{ backendStatusText }}</a-tag>
          </div>
        </div>

        <a-tabs v-model:activeKey="activeTab" class="editor-tabs">
          <a-tab-pane key="strategy" tab="生成策略">
            <div class="form-section">
              <div class="section-title">
                <span>数据来源 · 当前简历档案</span>
                <a-button size="small" @click="goToResumeEditor">去编辑简历</a-button>
              </div>
              <div class="grid-two">
                <div class="source-item">
                  <span>姓名</span>
                  <strong>{{ resumeSource.name || '未填写' }}</strong>
                </div>
                <div class="source-item">
                  <span>应聘岗位</span>
                  <strong>{{ resumeSource.applicationPosition || '未填写' }}</strong>
                </div>
                <div class="source-item">
                  <span>学校</span>
                  <strong>{{ resumeSource.university || '未填写' }}</strong>
                </div>
                <div class="source-item">
                  <span>专业</span>
                  <strong>{{ resumeSource.major || '未填写' }}</strong>
                </div>
              </div>
              <div class="source-counts">
                <a-tag v-for="item in sectionCounts" :key="item.label" class="count-tag">
                  {{ item.label }} {{ item.count }}
                </a-tag>
              </div>
              <p class="source-tip">
                技能、荣誉、自我评价与各段经历直接取自当前简历档案，生成时自动携带，无需重复填写。
              </p>
            </div>

            <div class="form-section">
              <div class="section-title">
                <span>模板与生成策略</span>
              </div>
              <div class="grid-two">
                <a-select
                  v-model:value="agentConfig.templateId"
                  :options="templateOptions"
                  placeholder="选择提示词模板"
                />
                <a-input v-model:value="agentConfig.targetRole" placeholder="目标岗位关键词，如前端开发 / 产品运营" />
              </div>
              <div v-if="selectedTemplate" class="template-card">
                <div class="template-title">
                  <strong>{{ selectedTemplate.name }}</strong>
                  <a-tag class="template-style-tag" color="blue">{{ selectedTemplate.style }}</a-tag>
                </div>
                <p>{{ selectedTemplate.description }}</p>
                <small>适用场景：{{ selectedTemplate.targetAudience }}</small>
              </div>
              <div class="inline-switch">
                <span>启用知识库检索增强（RAG）</span>
                <a-switch v-model:checked="agentConfig.enableRag" />
              </div>
              <div class="inline-switch" style="margin-top: 12px;">
                <span>简历正文字数控制</span>
                <a-slider v-model:value="agentConfig.wordCount" :min="300" :max="2000" :step="50" style="flex: 1; margin-left: 16px;" />
                <span style="min-width: 50px; text-align: right;">{{ agentConfig.wordCount }} 字</span>
              </div>
            </div>

            <div class="form-section">
              <div class="section-title">
                <span>补充生成信息</span>
              </div>
              <div class="grid-two">
                <a-input v-model:value="agentConfig.targetIndustry" placeholder="求职方向 / 行业" />
                <a-input v-model:value="agentConfig.ranking" placeholder="成绩 / 排名，如专业前10%" />
              </div>
              <a-textarea
                v-model:value="agentConfig.courses"
                :auto-size="{ minRows: 2, maxRows: 4 }"
                placeholder="核心课程，使用分号或换行分隔"
                style="margin-top: 12px;"
              />
              <a-textarea
                v-model:value="agentConfig.interests"
                :auto-size="{ minRows: 2, maxRows: 4 }"
                placeholder="兴趣爱好，可选"
                style="margin-top: 12px;"
              />
              <p class="source-tip">补充信息与生成策略会随当前简历档案一起保存，不同岗位档案可各自记忆。</p>
            </div>
          </a-tab-pane>

          <a-tab-pane key="knowledge" tab="知识库管理">
            <KnowledgeBasePanel />
          </a-tab-pane>

          <a-tab-pane v-if="isAdmin" key="model" tab="模型服务">
            <ModelConfigPanel />
          </a-tab-pane>
        </a-tabs>

        <div class="action-bar">
          <a-tooltip
            :title="health.status.value === 'down' ? '服务端离线，连接后可用' : '按当前档案数据与生成策略调用智能体'"
          >
            <a-button
              type="primary"
              :loading="generating"
              :disabled="health.status.value === 'down'"
              @click="handleGenerate"
            >
              生成结构化简历
            </a-button>
          </a-tooltip>
        </div>
      </section>

      <section class="right-panel">
        <div class="result-header">
          <div>
            <h2>生成结果预览</h2>
            <p>生成后可直接写回简历编辑器，再继续手工微调。</p>
          </div>
          <div class="result-actions">
            <a-button :disabled="!generatedResult" @click="applyResultToResume">应用到编辑器</a-button>
            <a-button type="primary" ghost :disabled="!generatedResult" @click="goToResumeEditor">
              去简历编辑页
            </a-button>
          </div>
        </div>

        <a-spin :spinning="pageLoading">
          <div class="status-cards">
            <div class="mini-card">
              <span>模板数量</span>
              <strong>{{ templates.length }}</strong>
            </div>
            <div class="mini-card">
              <span>当前生成模式</span>
              <strong>{{ generatedResult?.meta.provider || '未生成' }}</strong>
            </div>
          </div>

          <a-empty v-if="!generatedResult" description="还没有生成结果，确认档案信息后点击生成" />

          <template v-else>
            <a-alert
              v-if="generatedResult.meta.fallbackReason"
              type="warning"
              show-icon
              class="fallback-alert"
              :message="`本次为本地回退生成：${generatedResult.meta.fallbackReason}`"
              description="在「模型服务」中配置可用的模型接口后即可获得 AI 生成结果。"
            />

            <div class="result-card">
              <div class="card-head">
                <h3>生成元信息</h3>
                <a-tag class="template-style-tag" color="blue">{{ generatedResult.meta.templateName }}</a-tag>
              </div>
              <p>生成提供方：{{ generatedResult.meta.provider }}</p>
              <div class="tag-list">
                <a-tag
                  v-for="item in generatedResult.meta.knowledgeHits"
                  :key="item.documentId"
                  class="knowledge-hit-tag"
                  color="processing"
                >
                  {{ item.documentName }} · {{ item.category }} · {{ item.score }}
                </a-tag>
              </div>
            </div>

            <div class="result-card">
              <div class="card-head">
                <h3>个人总结</h3>
              </div>
              <p class="multiline">{{ generatedResult.resumeData.summary }}</p>
            </div>

            <div class="result-card">
              <div class="card-head">
                <h3>基本信息</h3>
              </div>
              <div class="info-grid">
                <div><span>姓名</span><strong>{{ generatedResult.resumeData.personalInfo.name || '-' }}</strong></div>
                <div><span>岗位</span><strong>{{ generatedResult.resumeData.personalInfo.applicationPosition || '-' }}</strong></div>
                <div><span>学校</span><strong>{{ generatedResult.resumeData.personalInfo.university || '-' }}</strong></div>
                <div><span>专业</span><strong>{{ generatedResult.resumeData.personalInfo.major || '-' }}</strong></div>
              </div>
            </div>

            <div class="result-card">
              <div class="card-head">
                <h3>教育经历</h3>
              </div>
              <div v-for="item in generatedResult.resumeData.education" :key="item.id" class="result-item">
                <strong>{{ item.school || '未填写学校' }}</strong>
                <span>{{ item.degree }} {{ item.major }}</span>
                <small>{{ item.startDate }} - {{ item.endDate }}</small>
              </div>
            </div>

            <div class="result-card">
              <div class="card-head">
                <h3>项目经历</h3>
              </div>
              <a-empty v-if="generatedResult.resumeData.projects.length === 0" description="暂无项目经历" />
              <div v-for="item in generatedResult.resumeData.projects" :key="item.id" class="result-item">
                <strong>{{ item.projectName }}</strong>
                <span>{{ item.role }}</span>
                <small>{{ item.startDate }} - {{ item.endDate }}</small>
                <p class="multiline">{{ item.description }}</p>
              </div>
            </div>

            <div class="result-card">
              <div class="card-head">
                <h3>工作经历</h3>
              </div>
              <a-empty v-if="generatedResult.resumeData.workExperience.length === 0" description="暂无工作经历" />
              <div v-for="item in generatedResult.resumeData.workExperience" :key="item.id" class="result-item">
                <strong>{{ item.company }}</strong>
                <span>{{ item.position }}</span>
                <small>{{ item.startDate }} - {{ item.endDate }}</small>
                <p class="multiline">{{ item.description }}</p>
              </div>
            </div>

            <div class="result-card">
              <div class="card-head">
                <h3>技能与奖项</h3>
              </div>
              <div class="tag-list">
                <a-tag v-for="item in generatedResult.resumeData.skills" :key="item.id" class="skill-tag" color="cyan">
                  {{ item.skillName }}
                </a-tag>
              </div>
              <div class="result-item" v-for="item in generatedResult.resumeData.honors" :key="item.id">
                <strong>{{ item.honorName }}</strong>
                <p class="multiline">{{ item.description }}</p>
              </div>
            </div>
          </template>
        </a-spin>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { message } from "ant-design-vue";
import { useRouter } from "vue-router";
import { generateResume, getPromptTemplates } from "../../api/agentAPI";
import { useResumeStore } from "../../store";
import { useBackendHealth } from "../../composables/useBackendHealth";
import { sectionLabels } from "../../constants/sectionLabels";
import { getSessionUser } from "../../utils/auth";
import KnowledgeBasePanel from "./components/KnowledgeBasePanel.vue";
import ModelConfigPanel from "./components/ModelConfigPanel.vue";
import type { GeneratedResumeResponse, PromptTemplate, ResumeGenerateRequest } from "../../types/agent";

const router = useRouter();
const resumeStore = useResumeStore();
const health = useBackendHealth();
// 模型服务配置仅运营者可见(后端接口另有 admin 鉴权兜底)
const isAdmin = getSessionUser()?.role === "admin";

const activeTab = ref("strategy");
const generating = ref(false);
const pageLoading = ref(false);
const templates = ref<PromptTemplate[]>([]);
const generatedResult = ref<GeneratedResumeResponse | null>(null);

// 生成策略直接落在简历档案上,随档案保存与切换
const agentConfig = computed(() => resumeStore.agentConfig);

const templateOptions = computed(() =>
  templates.value.map((item) => ({
    value: item.id,
    label: item.name
  }))
);

const selectedTemplate = computed(() =>
  templates.value.find((item) => item.id === agentConfig.value.templateId) || null
);

const backendStatusText = computed(() => {
  if (health.status.value === 'down') return "离线";
  if (health.status.value === 'unknown') return "检测中";
  return health.info.value?.provider === "llm-configured" ? "已连接模型接口" : "本地回退模式";
});

const backendStatusColor = computed(() => {
  if (health.status.value === 'down') return "error";
  if (health.status.value === 'unknown') return "default";
  return health.info.value?.provider === "llm-configured" ? "success" : "gold";
});

// 数据来源摘要:全部来自当前简历档案
const resumeSource = computed(() => ({
  name: resumeStore.personalInfo.name,
  applicationPosition: resumeStore.personalInfo.applicationPosition,
  university: resumeStore.personalInfo.university,
  major: resumeStore.personalInfo.major
}));

const sectionCounts = computed(() => [
  { label: sectionLabels.education, count: resumeStore.education.length },
  { label: sectionLabels.projects, count: resumeStore.projects.length },
  { label: sectionLabels.workExperience, count: resumeStore.workExperience.length },
  { label: sectionLabels.skills, count: resumeStore.skills.length },
  { label: sectionLabels.honors, count: resumeStore.honors.length }
]);

// 从当前简历档案 + 生成策略组装请求,不再维护第二份表单
function buildGenerateRequest(): ResumeGenerateRequest {
  const info = resumeStore.personalInfo;
  return {
    name: info.name,
    gender: info.gender,
    age: info.age,
    phone: info.phone,
    email: info.email,
    website: info.website,
    school: info.university,
    major: info.major,
    degree: resumeStore.education[0]?.degree || "",
    politicalStatus: info.politicalStatus,
    applicationPosition: info.applicationPosition,
    targetRole: agentConfig.value.targetRole || info.applicationPosition,
    targetIndustry: agentConfig.value.targetIndustry,
    ranking: agentConfig.value.ranking,
    courses: agentConfig.value.courses,
    skillsText: resumeStore.skills.map((item) => item.skillName).filter(Boolean).join("\n"),
    honorsText: resumeStore.honors.map((item) => item.honorName).filter(Boolean).join("\n"),
    interests: agentConfig.value.interests,
    selfIntroduction: resumeStore.summary,
    templateId: agentConfig.value.templateId,
    enableRag: agentConfig.value.enableRag,
    wordCount: agentConfig.value.wordCount,
    educationExperiences: resumeStore.education.map((item) => ({
      school: item.school,
      degree: item.degree,
      major: item.major,
      startDate: item.startDate,
      endDate: item.endDate
    })),
    workExperiences: resumeStore.workExperience.map((item) => ({
      company: item.company,
      position: item.position,
      startDate: item.startDate || "",
      endDate: item.endDate || "",
      description: item.description
    })),
    projectExperiences: resumeStore.projects.map((item) => ({
      projectName: item.projectName,
      role: item.role,
      startDate: item.startDate,
      endDate: item.endDate,
      briefIntroduction: item.briefIntroduction,
      description: item.description
    }))
  };
}

function validateGenerate() {
  const request = buildGenerateRequest();
  if (!request.name.trim()) {
    message.warning("请先在简历档案中填写姓名");
    return false;
  }
  if (!request.school.trim()) {
    message.warning("请先在简历档案中填写学校");
    return false;
  }
  if (!request.templateId) {
    message.warning("请选择提示词模板");
    return false;
  }
  return true;
}

async function loadInitialData() {
  pageLoading.value = true;
  try {
    templates.value = await getPromptTemplates();
    if (!agentConfig.value.templateId && templates.value.length > 0) {
      agentConfig.value.templateId = templates.value[0].id;
    }
  } catch (error) {
    console.error(error);
    message.error("提示词模板加载失败，请检查服务端连接。");
  } finally {
    pageLoading.value = false;
  }
}

async function handleGenerate() {
  if (health.status.value === 'down') {
    message.warning("服务端离线，请先在账号与设置中配置并启动服务端");
    return;
  }
  if (!validateGenerate()) return;

  generating.value = true;
  try {
    generatedResult.value = await generateResume(buildGenerateRequest());
    message.success("智能体已生成结构化简历");
  } catch (error) {
    console.error(error);
    message.error("生成失败，请检查后端是否启动或模型接口配置是否正确");
  } finally {
    generating.value = false;
  }
}

function applyResultToResume() {
  if (!generatedResult.value) return;
  resumeStore.applyGeneratedResume(generatedResult.value.resumeData);
}

function goToResumeEditor() {
  router.push("/");
}

onMounted(() => {
  loadInitialData();
});
</script>

<style scoped>
.agent-page {
  min-height: calc(100vh - 60px);
  padding: 24px;
  background: var(--stage-gradient);
}

.workspace {
  display: grid;
  grid-template-columns: minmax(540px, 1.05fr) minmax(420px, 0.95fr);
  gap: 20px;
  min-height: calc(100vh - 108px);
}

.left-panel,
.right-panel {
  border-radius: 22px;
  border: 1px solid var(--border-color);
  background: var(--panel-gradient);
  box-shadow: var(--panel-shadow);
}

.left-panel {
  padding: 22px;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.right-panel {
  padding: 22px;
  overflow-y: auto;
}

.panel-header,
.result-header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
}

.panel-header h1,
.result-header h2,
.card-head h3,
.result-item strong,
.template-card strong,
.mini-card strong {
  margin: 0;
  color: var(--text-color);
}

.panel-header p,
.result-header p,
.result-card > p,
.template-card p,
.source-tip {
  margin: 6px 0 0;
  color: var(--text-muted);
  font-size: 13px;
  line-height: 1.6;
}

.panel-header h1 {
  font-size: 24px;
}

.status-box {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
  padding: 8px 12px;
  border-radius: 12px;
  background: var(--inset-bg);
  min-width: 120px;
}

.status-label {
  color: var(--text-muted);
  font-size: 12px;
}

.editor-tabs {
  flex: 1;
  min-height: 0;
  margin-top: 16px;
}

.form-section {
  margin-bottom: 20px;
  padding: 18px;
  border-radius: 16px;
  background: var(--inset-bg);
  border: 1px solid var(--border-color);
}

.section-title,
.card-tools,
.card-head,
.template-title,
.result-actions,
.inline-switch {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.section-title {
  margin-bottom: 14px;
  color: var(--text-color);
  font-weight: 600;
}

.grid-two {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.source-item {
  padding: 12px 14px;
  border-radius: 12px;
  background: var(--inset-bg-strong);
  border: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.source-item span {
  color: var(--text-muted);
  font-size: 12px;
}

.source-item strong {
  color: var(--text-color);
  font-size: 15px;
}

.source-counts {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}

.count-tag {
  background: var(--inset-bg-strong);
}

.source-tip {
  margin-top: 12px;
}

.template-card {
  margin-top: 12px;
  padding: 14px;
  border-radius: 14px;
  background: var(--inset-bg-strong);
  border: 1px solid var(--border-color);
}

.template-card p {
  margin: 8px 0;
  color: var(--text-muted);
  font-size: 13px;
  line-height: 1.6;
}

.template-card small {
  color: var(--text-muted);
}

.form-section :deep(.ant-input),
.form-section :deep(.ant-select),
.form-section :deep(.ant-input-affix-wrapper),
.form-section :deep(.ant-input-number),
.form-section :deep(.ant-input-textarea) {
  margin-bottom: 12px;
}

.result-card,
.template-card,
.mini-card {
  border-radius: 14px;
  border: 1px solid var(--border-color);
  background: var(--inset-bg-strong);
}

.result-card {
  padding: 16px;
}

.result-card + .result-card {
  margin-top: 14px;
}

.card-tools {
  margin-bottom: 12px;
  color: var(--text-color);
}

.template-card p,
.result-item p {
  white-space: pre-wrap;
  line-height: 1.7;
  color: var(--text-muted);
}

.template-card small {
  color: var(--text-muted);
}

.inline-switch {
  margin-top: 8px;
  color: var(--text-color);
}

.config-grid,
.status-cards,
.info-grid {
  display: grid;
  gap: 12px;
}

.config-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.mini-card,
.info-grid > div {
  padding: 14px;
  border-radius: 14px;
  background: var(--inset-bg-strong);
  border: 1px solid var(--border-color);
}

.mini-card span,
.info-grid span {
  display: block;
  margin-bottom: 8px;
  color: var(--text-muted);
  font-size: 12px;
}

.mini-card strong,
.info-grid strong {
  color: var(--text-color);
  font-size: 15px;
}

.result-item span,
.result-item small {
  margin: 4px 0 0;
  display: block;
  color: var(--text-muted);
}

.action-bar {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding-top: 10px;
}

.result-header {
  margin-bottom: 18px;
}

.fallback-alert {
  margin-bottom: 14px;
}

.status-cards {
  grid-template-columns: repeat(3, minmax(0, 1fr));
  margin-bottom: 16px;
}

.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.status-tag,
.template-style-tag,
.knowledge-hit-tag,
.skill-tag,
.count-tag {
  border: 1px solid var(--border-color) !important;
  background: var(--inset-bg-strong) !important;
  color: var(--text-color) !important;
}

.result-item + .result-item {
  margin-top: 12px;
}

@media (max-width: 1380px) {
  .workspace {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .agent-page {
    min-height: 100svh;
    padding: 12px;
  }

  .workspace {
    display: block;
    min-height: 0;
  }

  .left-panel,
  .right-panel {
    padding: 14px;
    border-radius: 14px;
  }

  .right-panel {
    margin-top: 12px;
  }

  .panel-header,
  .result-header,
  .section-title,
  .card-tools,
  .card-head,
  .template-title,
  .result-actions,
  .inline-switch,
  .action-bar {
    align-items: stretch;
    flex-direction: column;
  }

  .panel-header h1 {
    font-size: 22px;
    line-height: 1.25;
  }

  .result-header h2 {
    font-size: 20px;
  }

  .status-box {
    min-width: 0;
    text-align: left;
  }

  .form-section {
    padding: 14px;
    border-radius: 12px;
  }

  .grid-two,
  .config-grid,
  .status-cards,
  .info-grid {
    grid-template-columns: 1fr;
  }

  .result-actions :deep(.ant-btn),
  .action-bar :deep(.ant-btn),
  .form-section > :deep(.ant-btn) {
    width: 100%;
  }

  .editor-tabs :deep(.ant-tabs-nav) {
    overflow-x: auto;
  }

  .editor-tabs :deep(.ant-tabs-nav-list) {
    min-width: max-content;
  }
}
</style>
