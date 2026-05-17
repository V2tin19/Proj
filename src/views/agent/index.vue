<template>
  <div class="agent-page">
    <div class="workspace">
      <section class="left-panel">
        <div class="panel-header">
          <div>
            <h1>简历智能体工作台</h1>
            <p>先录入学生信息，再调用后端生成结构化简历，并可一键回填到编辑器。</p>
          </div>
          <div class="status-box">
            <span class="status-label">后端状态</span>
            <a-tag class="status-tag" :color="backendStatusColor">{{ backendStatusText }}</a-tag>
          </div>
        </div>

        <a-alert
          message="当前阶段说明"
          description="这一版先实现本地后端、提示词模板、知识库配置、RAG 检索和结构化简历生成闭环。后续可以继续接本地 DeepSeek/Qwen 模型、文件上传解析和 Word 导出。"
          type="info"
          show-icon
          class="intro-alert"
        />

        <a-tabs v-model:activeKey="activeTab" class="editor-tabs">
          <a-tab-pane key="profile" tab="学生信息">
            <div class="form-section">
              <div class="section-title">
                <span>基础信息</span>
                <a-button size="small" @click="fillFromResumeStore">从当前简历回填</a-button>
              </div>
              <div class="grid-two">
                <a-input v-model:value="form.name" placeholder="姓名" />
                <a-input v-model:value="form.gender" placeholder="性别" />
                <a-input v-model:value="form.age" placeholder="年龄" />
                <a-input v-model:value="form.phone" placeholder="手机号" />
                <a-input v-model:value="form.email" placeholder="邮箱" />
                <a-input v-model:value="form.website" placeholder="个人主页 / GitHub" />
                <a-input v-model:value="form.school" placeholder="学校" />
                <a-input v-model:value="form.major" placeholder="专业" />
                <a-input v-model:value="form.degree" placeholder="学历 / 学位" />
                <a-input v-model:value="form.politicalStatus" placeholder="政治面貌" />
                <a-input v-model:value="form.applicationPosition" placeholder="应聘岗位" />
                <a-input v-model:value="form.targetIndustry" placeholder="求职方向 / 行业" />
              </div>
            </div>

            <div class="form-section">
              <div class="section-title">
                <span>模板与生成策略</span>
              </div>
              <div class="grid-two">
                <a-select
                  v-model:value="form.templateId"
                  :options="templateOptions"
                  placeholder="选择提示词模板"
                />
                <a-input v-model:value="form.targetRole" placeholder="目标岗位关键词，如前端开发 / 产品运营" />
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
                <a-switch v-model:checked="form.enableRag" />
              </div>
            </div>

            <div class="form-section">
              <div class="section-title">
                <span>教育经历</span>
                <a-button size="small" type="dashed" @click="addEducationRow">新增</a-button>
              </div>
              <div
                v-for="(item, index) in form.educationExperiences"
                :key="`education-${index}`"
                class="experience-card"
              >
                <div class="card-tools">
                  <span>教育经历 {{ index + 1 }}</span>
                  <a-button size="small" danger ghost @click="removeEducationRow(index)">删除</a-button>
                </div>
                <div class="grid-two">
                  <a-input v-model:value="item.school" placeholder="学校" />
                  <a-input v-model:value="item.degree" placeholder="学历 / 学位" />
                  <a-input v-model:value="item.major" placeholder="专业" />
                  <a-input v-model:value="item.startDate" placeholder="开始时间" />
                  <a-input v-model:value="item.endDate" placeholder="结束时间" />
                </div>
              </div>
            </div>

            <div class="form-section">
              <div class="section-title">
                <span>项目经历</span>
                <a-button size="small" type="dashed" @click="addProjectRow">新增</a-button>
              </div>
              <div
                v-for="(item, index) in form.projectExperiences"
                :key="`project-${index}`"
                class="experience-card"
              >
                <div class="card-tools">
                  <span>项目经历 {{ index + 1 }}</span>
                  <a-button size="small" danger ghost @click="removeProjectRow(index)">删除</a-button>
                </div>
                <div class="grid-two">
                  <a-input v-model:value="item.projectName" placeholder="项目名称" />
                  <a-input v-model:value="item.role" placeholder="角色" />
                  <a-input v-model:value="item.startDate" placeholder="开始时间" />
                  <a-input v-model:value="item.endDate" placeholder="结束时间" />
                </div>
                <a-input
                  v-model:value="item.briefIntroduction"
                  placeholder="项目一句话简介"
                  class="block-field"
                />
                <a-textarea
                  v-model:value="item.description"
                  :auto-size="{ minRows: 3, maxRows: 6 }"
                  placeholder="按行填写职责、难点、成果，例如：负责页面开发；封装组件；优化首屏性能。"
                />
              </div>
            </div>

            <div class="form-section">
              <div class="section-title">
                <span>实践 / 实习经历</span>
                <a-button size="small" type="dashed" @click="addWorkRow">新增</a-button>
              </div>
              <div
                v-for="(item, index) in form.workExperiences"
                :key="`work-${index}`"
                class="experience-card"
              >
                <div class="card-tools">
                  <span>实践经历 {{ index + 1 }}</span>
                  <a-button size="small" danger ghost @click="removeWorkRow(index)">删除</a-button>
                </div>
                <div class="grid-two">
                  <a-input v-model:value="item.company" placeholder="公司 / 单位 / 组织" />
                  <a-input v-model:value="item.position" placeholder="岗位 / 身份" />
                  <a-input v-model:value="item.startDate" placeholder="开始时间" />
                  <a-input v-model:value="item.endDate" placeholder="结束时间" />
                </div>
                <a-textarea
                  v-model:value="item.description"
                  :auto-size="{ minRows: 3, maxRows: 6 }"
                  placeholder="按行填写职责与成果。"
                />
              </div>
            </div>

            <div class="form-section">
              <div class="section-title">
                <span>补充信息</span>
              </div>
              <div class="grid-two">
                <a-input v-model:value="form.ranking" placeholder="成绩 / 排名，如专业前10%" />
                <a-input v-model:value="form.courses" placeholder="核心课程，使用分号或换行分隔" />
              </div>
              <a-textarea
                v-model:value="form.skillsText"
                :auto-size="{ minRows: 3, maxRows: 6 }"
                placeholder="技能清单，建议一行一项"
              />
              <a-textarea
                v-model:value="form.honorsText"
                :auto-size="{ minRows: 3, maxRows: 6 }"
                placeholder="荣誉奖项，建议一行一项"
              />
              <a-textarea
                v-model:value="form.interests"
                :auto-size="{ minRows: 2, maxRows: 4 }"
                placeholder="兴趣爱好，可选"
              />
              <a-textarea
                v-model:value="form.selfIntroduction"
                :auto-size="{ minRows: 4, maxRows: 8 }"
                placeholder="个人总结、自我介绍、优势亮点"
              />
            </div>
          </a-tab-pane>

          <a-tab-pane key="knowledge" tab="知识库管理">
            <div class="form-section">
              <div class="section-title">
                <span>知识库配置</span>
                <a-button size="small" @click="loadKnowledgeBaseResources">刷新</a-button>
              </div>
              <div v-if="knowledgeBaseConfig" class="config-grid">
                <div class="config-item">
                  <span>分块大小</span>
                  <strong>{{ knowledgeBaseConfig.chunkSize }}</strong>
                </div>
                <div class="config-item">
                  <span>分块重叠</span>
                  <strong>{{ knowledgeBaseConfig.chunkOverlap }}</strong>
                </div>
                <div class="config-item">
                  <span>Top K</span>
                  <strong>{{ knowledgeBaseConfig.retrievalTopK }}</strong>
                </div>
                <div class="config-item">
                  <span>匹配算法</span>
                  <strong>{{ knowledgeBaseConfig.matchAlgorithm }}</strong>
                </div>
                <div class="config-item">
                  <span>向量/检索实现</span>
                  <strong>{{ knowledgeBaseConfig.embeddingProvider }}</strong>
                </div>
              </div>
            </div>

            <div class="form-section">
              <div class="section-title">
                <span>新增知识条目</span>
              </div>
              <div class="grid-two">
                <a-input v-model:value="knowledgeForm.name" placeholder="文档名称" />
                <a-input v-model:value="knowledgeForm.category" placeholder="分类，如技术岗 / 写作规范" />
              </div>
              <a-textarea
                v-model:value="knowledgeForm.content"
                :auto-size="{ minRows: 5, maxRows: 8 }"
                placeholder="粘贴简历模板规范、岗位描述经验、优秀案例要点等文本内容"
              />
              <a-button type="primary" :loading="savingKnowledge" @click="submitKnowledgeDocument">
                保存到知识库
              </a-button>
            </div>

            <div class="form-section">
              <div class="section-title">
                <span>已有知识条目</span>
              </div>
              <a-empty v-if="knowledgeDocuments.length === 0" description="暂时还没有知识条目" />
              <div v-else class="knowledge-list">
                <div v-for="item in knowledgeDocuments" :key="item.id" class="knowledge-card">
                  <div class="knowledge-top">
                    <div>
                      <strong>{{ item.name }}</strong>
                      <p>{{ item.category }}</p>
                    </div>
                    <a-popconfirm
                      title="确定删除这个知识条目吗？"
                      ok-text="删除"
                      cancel-text="取消"
                      @confirm="removeKnowledge(item.id)"
                    >
                      <a-button size="small" danger ghost>删除</a-button>
                    </a-popconfirm>
                  </div>
                  <p class="knowledge-content">{{ item.content }}</p>
                </div>
              </div>
            </div>
          </a-tab-pane>
        </a-tabs>

        <div class="action-bar">
          <a-button @click="fillFromResumeStore">重置为当前简历</a-button>
          <a-button type="primary" :loading="generating" @click="handleGenerate">
            生成结构化简历
          </a-button>
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
              <span>知识条目</span>
              <strong>{{ knowledgeDocuments.length }}</strong>
            </div>
            <div class="mini-card">
              <span>当前生成模式</span>
              <strong>{{ generatedResult?.meta.provider || '未生成' }}</strong>
            </div>
          </div>

          <a-empty v-if="!generatedResult" description="还没有生成结果，左侧填写信息后点击生成" />

          <template v-else>
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
                <h3>实践经历</h3>
              </div>
              <a-empty v-if="generatedResult.resumeData.workExperience.length === 0" description="暂无实践经历" />
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
import { computed, onMounted, reactive, ref } from "vue";
import { message } from "ant-design-vue";
import { useRouter } from "vue-router";
import {
  createKnowledgeDocument,
  deleteKnowledgeDocument,
  generateResume,
  getBackendHealth,
  getKnowledgeBaseConfig,
  getKnowledgeDocuments,
  getPromptTemplates
} from "../../api/agentAPI";
import { useResumeStore } from "../../store";
import type {
  GeneratedResumeResponse,
  KnowledgeBaseConfig,
  KnowledgeDocument,
  PromptTemplate,
  ResumeGenerateRequest,
  StudentEducationInput,
  StudentProjectInput,
  StudentWorkInput
} from "../../types/agent";

const router = useRouter();
const resumeStore = useResumeStore();

const activeTab = ref("profile");
const generating = ref(false);
const savingKnowledge = ref(false);
const pageLoading = ref(false);
const templates = ref<PromptTemplate[]>([]);
const knowledgeBaseConfig = ref<KnowledgeBaseConfig | null>(null);
const knowledgeDocuments = ref<KnowledgeDocument[]>([]);
const generatedResult = ref<GeneratedResumeResponse | null>(null);
const backendHealth = ref<{ ok: boolean; now: string; provider: string } | null>(null);

const createEmptyEducation = (): StudentEducationInput => ({
  school: "",
  degree: "",
  major: "",
  startDate: "",
  endDate: ""
});

const createEmptyProject = (): StudentProjectInput => ({
  projectName: "",
  role: "",
  startDate: "",
  endDate: "",
  briefIntroduction: "",
  description: ""
});

const createEmptyWork = (): StudentWorkInput => ({
  company: "",
  position: "",
  startDate: "",
  endDate: "",
  description: ""
});

const form = reactive<ResumeGenerateRequest>({
  name: "",
  gender: "",
  age: "",
  phone: "",
  email: "",
  website: "",
  school: "",
  major: "",
  degree: "",
  politicalStatus: "",
  applicationPosition: "",
  targetRole: "",
  targetIndustry: "",
  ranking: "",
  courses: "",
  skillsText: "",
  honorsText: "",
  interests: "",
  selfIntroduction: "",
  templateId: "",
  enableRag: true,
  educationExperiences: [createEmptyEducation()],
  workExperiences: [createEmptyWork()],
  projectExperiences: [createEmptyProject()]
});

const knowledgeForm = reactive({
  name: "",
  category: "",
  content: ""
});

const templateOptions = computed(() =>
  templates.value.map((item) => ({
    value: item.id,
    label: item.name
  }))
);

const selectedTemplate = computed(() =>
  templates.value.find((item) => item.id === form.templateId) || null
);

const backendStatusText = computed(() => {
  if (!backendHealth.value) return "未连接";
  return backendHealth.value.provider === "llm-configured" ? "已连接模型接口" : "本地回退模式";
});

const backendStatusColor = computed(() => {
  if (!backendHealth.value) return "default";
  return backendHealth.value.provider === "llm-configured" ? "success" : "gold";
});

function replaceArray<T>(target: T[], nextItems: T[]) {
  target.splice(0, target.length, ...nextItems);
}

function fillFromResumeStore() {
  form.name = resumeStore.personalInfo.name;
  form.gender = resumeStore.personalInfo.gender;
  form.age = resumeStore.personalInfo.age;
  form.phone = resumeStore.personalInfo.phone;
  form.email = resumeStore.personalInfo.email;
  form.website = resumeStore.personalInfo.website;
  form.school = resumeStore.personalInfo.university;
  form.major = resumeStore.personalInfo.major;
  form.degree = resumeStore.education[0]?.degree || "";
  form.politicalStatus = resumeStore.personalInfo.politicalStatus;
  form.applicationPosition = resumeStore.personalInfo.applicationPosition;
  form.targetRole = resumeStore.personalInfo.applicationPosition;
  form.skillsText = resumeStore.skills.map((item) => item.skillName).filter(Boolean).join("\n");
  form.honorsText = resumeStore.honors.map((item) => item.honorName).filter(Boolean).join("\n");
  form.selfIntroduction = resumeStore.summary;

  replaceArray(
    form.educationExperiences,
    resumeStore.education.length
      ? resumeStore.education.map((item) => ({
          school: item.school,
          degree: item.degree,
          major: item.major,
          startDate: item.startDate,
          endDate: item.endDate
        }))
      : [createEmptyEducation()]
  );

  replaceArray(
    form.projectExperiences,
    resumeStore.projects.length
      ? resumeStore.projects.map((item) => ({
          projectName: item.projectName,
          role: item.role,
          startDate: item.startDate,
          endDate: item.endDate,
          briefIntroduction: item.briefIntroduction,
          description: item.description
        }))
      : [createEmptyProject()]
  );

  replaceArray(
    form.workExperiences,
    resumeStore.workExperience.length
      ? resumeStore.workExperience.map((item) => ({
          company: item.company,
          position: item.position,
          startDate: item.startDate || "",
          endDate: item.endDate || "",
          description: item.description
        }))
      : [createEmptyWork()]
  );
}

function addEducationRow() {
  form.educationExperiences.push(createEmptyEducation());
}

function removeEducationRow(index: number) {
  if (form.educationExperiences.length === 1) {
    replaceArray(form.educationExperiences, [createEmptyEducation()]);
    return;
  }
  form.educationExperiences.splice(index, 1);
}

function addProjectRow() {
  form.projectExperiences.push(createEmptyProject());
}

function removeProjectRow(index: number) {
  if (form.projectExperiences.length === 1) {
    replaceArray(form.projectExperiences, [createEmptyProject()]);
    return;
  }
  form.projectExperiences.splice(index, 1);
}

function addWorkRow() {
  form.workExperiences.push(createEmptyWork());
}

function removeWorkRow(index: number) {
  if (form.workExperiences.length === 1) {
    replaceArray(form.workExperiences, [createEmptyWork()]);
    return;
  }
  form.workExperiences.splice(index, 1);
}

async function loadKnowledgeBaseResources() {
  const [config, documents] = await Promise.all([
    getKnowledgeBaseConfig(),
    getKnowledgeDocuments()
  ]);
  knowledgeBaseConfig.value = config;
  knowledgeDocuments.value = documents;
}

async function loadInitialData() {
  pageLoading.value = true;
  try {
    const [health, promptTemplates] = await Promise.all([
      getBackendHealth(),
      getPromptTemplates()
    ]);

    backendHealth.value = health;
    templates.value = promptTemplates;
    if (!form.templateId && promptTemplates.length > 0) {
      form.templateId = promptTemplates[0].id;
    }

    await loadKnowledgeBaseResources();
    fillFromResumeStore();
  } catch (error) {
    console.error(error);
    message.error("智能体后端暂时不可用，请先启动本地服务。");
  } finally {
    pageLoading.value = false;
  }
}

async function submitKnowledgeDocument() {
  if (!knowledgeForm.name.trim() || !knowledgeForm.content.trim()) {
    message.warning("请先填写文档名称和内容");
    return;
  }

  savingKnowledge.value = true;
  try {
    await createKnowledgeDocument({
      name: knowledgeForm.name,
      category: knowledgeForm.category || "未分类",
      content: knowledgeForm.content
    });
    knowledgeForm.name = "";
    knowledgeForm.category = "";
    knowledgeForm.content = "";
    await loadKnowledgeBaseResources();
    message.success("知识条目已写入本地知识库");
  } catch (error) {
    console.error(error);
    message.error("保存知识条目失败");
  } finally {
    savingKnowledge.value = false;
  }
}

async function removeKnowledge(documentId: string) {
  try {
    await deleteKnowledgeDocument(documentId);
    knowledgeDocuments.value = knowledgeDocuments.value.filter((item) => item.id !== documentId);
    message.success("知识条目已删除");
  } catch (error) {
    console.error(error);
    message.error("删除知识条目失败");
  }
}

function validateGenerateForm() {
  if (!form.name.trim()) {
    message.warning("请至少填写姓名");
    return false;
  }
  if (!form.school.trim()) {
    message.warning("请至少填写学校");
    return false;
  }
  if (!form.templateId) {
    message.warning("请选择提示词模板");
    return false;
  }
  return true;
}

async function handleGenerate() {
  if (!validateGenerateForm()) return;

  generating.value = true;
  try {
    generatedResult.value = await generateResume({
      ...form,
      educationExperiences: form.educationExperiences.map((item) => ({ ...item })),
      workExperiences: form.workExperiences.map((item) => ({ ...item })),
      projectExperiences: form.projectExperiences.map((item) => ({ ...item }))
    });
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
  background:
    radial-gradient(circle at top, rgba(45, 91, 255, 0.12), transparent 24%),
    linear-gradient(180deg, #0a111b 0%, #070b12 100%);
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
  background:
    linear-gradient(180deg, rgba(16, 23, 34, 0.96), rgba(10, 17, 27, 0.98));
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.22);
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
.knowledge-top strong,
.template-card strong,
.mini-card strong {
  margin: 0;
  color: var(--text-color);
}

.panel-header p,
.result-header p,
.result-card > p,
.knowledge-top p {
  margin: 8px 0 0;
  color: var(--text-muted);
  line-height: 1.6;
}

.status-box {
  min-width: 120px;
  text-align: right;
}

.status-label {
  display: block;
  margin-bottom: 8px;
  color: var(--text-muted);
  font-size: 12px;
}

.intro-alert {
  margin: 18px 0;
}

.intro-alert :deep(.ant-alert-message) {
  color: var(--text-color) !important;
  font-weight: 600;
}

.intro-alert :deep(.ant-alert-description) {
  color: var(--text-muted) !important;
}

.intro-alert :deep(.ant-alert-icon) {
  color: #7ea2ff !important;
}

.editor-tabs {
  flex: 1;
  min-height: 0;
}

.form-section {
  margin-bottom: 20px;
  padding: 18px;
  border-radius: 16px;
  background: rgba(11, 18, 29, 0.82);
  border: 1px solid rgba(80, 100, 140, 0.18);
}

.section-title,
.card-tools,
.knowledge-top,
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

.block-field,
.form-section :deep(.ant-input),
.form-section :deep(.ant-select),
.form-section :deep(.ant-input-affix-wrapper),
.form-section :deep(.ant-input-number),
.form-section :deep(.ant-input-textarea) {
  margin-bottom: 12px;
}

.experience-card,
.knowledge-card,
.result-card,
.template-card,
.mini-card {
  border-radius: 14px;
  border: 1px solid rgba(80, 100, 140, 0.18);
  background: rgba(15, 23, 36, 0.9);
}

.experience-card,
.knowledge-card,
.result-card,
.template-card {
  padding: 16px;
}

.experience-card + .experience-card,
.knowledge-card + .knowledge-card,
.result-card + .result-card {
  margin-top: 14px;
}

.card-tools {
  margin-bottom: 12px;
  color: var(--text-color);
}

.template-card p,
.knowledge-content,
.multiline,
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

.config-item,
.mini-card,
.info-grid > div {
  padding: 14px;
  border-radius: 14px;
  background: rgba(15, 23, 36, 0.9);
  border: 1px solid rgba(80, 100, 140, 0.18);
}

.config-item span,
.mini-card span,
.info-grid span {
  display: block;
  margin-bottom: 8px;
  color: var(--text-muted);
  font-size: 12px;
}

.config-item strong,
.mini-card strong,
.info-grid strong {
  color: var(--text-color);
  font-size: 15px;
}

.knowledge-top p,
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
.skill-tag {
  border: 1px solid rgba(90, 116, 170, 0.28) !important;
  color: #dfe8ff !important;
}

.status-tag {
  background: rgba(45, 91, 255, 0.16) !important;
}

.template-style-tag {
  background: rgba(59, 108, 255, 0.18) !important;
}

.knowledge-hit-tag {
  background: rgba(38, 84, 170, 0.18) !important;
}

.skill-tag {
  background: rgba(32, 112, 132, 0.2) !important;
}

.result-item + .result-item {
  margin-top: 12px;
}

@media (max-width: 1380px) {
  .workspace {
    grid-template-columns: 1fr;
  }
}
</style>
