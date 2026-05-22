function ensureArray(value) {
  return Array.isArray(value) ? value : [];
}

function splitLines(text = "") {
  return String(text)
    .split(/\r?\n|[;；]/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function formatBulletSummary(lines, fallback) {
  const items = splitLines(lines);
  if (items.length === 0) return fallback;
  return items.map((item) => `- ${item}`).join("\n");
}

function summarizeKnowledge(references) {
  if (!references.length) return "";
  return references
    .map((item) => `${item.documentName}提示：${item.content}`)
    .join("\n");
}

function buildPromptPayload(input, template, references) {
  return {
    template,
    studentProfile: input,
    knowledgeReferences: references.map((item) => ({
      documentName: item.documentName,
      category: item.category,
      excerpt: item.content
    }))
  };
}

async function callOpenAICompatibleModel(input, template, references) {
  const apiUrl = process.env.LLM_API_URL || process.env.OPENAI_COMPATIBLE_API_URL;
  const apiKey = process.env.LLM_API_KEY || process.env.OPENAI_API_KEY;
  const model = process.env.LLM_MODEL || process.env.OPENAI_MODEL || "qwen-plus";

  if (!apiUrl || !apiKey) {
    return null;
  }

  const systemPrompt = `${template.systemPrompt}\n你必须输出 JSON，字段结构为：personalInfo、education、workExperience、skills、projects、honors、summary。不要输出 markdown。`;
  const userPrompt = JSON.stringify(buildPromptPayload(input, template, references), null, 2);

  const response = await fetch(apiUrl, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${apiKey}`
    },
    body: JSON.stringify({
      model,
      temperature: 0.4,
      response_format: { type: "json_object" },
      messages: [
        { role: "system", content: systemPrompt },
        { role: "user", content: userPrompt }
      ]
    })
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`LLM request failed: ${response.status} ${errorText}`);
  }

  const result = await response.json();
  const content = result?.choices?.[0]?.message?.content;
  if (!content) {
    throw new Error("LLM response missing content");
  }

  return JSON.parse(content);
}

function generateLocalResume(input, template, references) {
  const educationItems = ensureArray(input.educationExperiences).map((item, index) => ({
    id: index + 1,
    school: item.school || input.school || "",
    degree: item.degree || input.degree || "",
    major: item.major || input.major || "",
    startDate: item.startDate || "",
    endDate: item.endDate || "",
  }));

  const workItems = ensureArray(input.workExperiences).map((item, index) => ({
    id: 100 + index,
    company: item.company || "",
    position: item.position || "",
    startDate: item.startDate || "",
    endDate: item.endDate || "",
    description: formatBulletSummary(
      item.description,
      "负责相关工作内容，参与项目执行并完成阶段性成果。"
    )
  }));

  const projectItems = ensureArray(input.projectExperiences).map((item, index) => ({
    id: 200 + index,
    projectName: item.projectName || "",
    role: item.role || "项目成员",
    startDate: item.startDate || "",
    endDate: item.endDate || "",
    briefIntroduction: item.briefIntroduction || item.projectName || "",
    description: formatBulletSummary(
      item.description,
      "围绕项目目标完成方案设计、实现与优化，并沉淀项目成果。"
    )
  }));

  const skillItems = splitLines(input.skillsText).map((skillName, index) => ({
    id: 300 + index,
    skillName
  }));

  const honorItems = splitLines(input.honorsText).map((honorName, index) => ({
    id: 400 + index,
    honorName,
    date: "",
    description: "由智能体根据学生提供信息自动整理。"
  }));

  const courseText = splitLines(input.courses).join("、");
  const rankingText = input.ranking ? `成绩/排名：${input.ranking}` : "";
  const interestsText = splitLines(input.interests).join("、");
  const knowledgeSummary = summarizeKnowledge(references);
  const experienceCount = projectItems.length + workItems.length;

  const summaryParts = [
    `${input.name || "该同学"}面向${input.targetRole || input.applicationPosition || "目标岗位"}进行求职，整体风格采用“${template.name}”。`,
    input.selfIntroduction || "",
    courseText ? `课程基础涵盖：${courseText}。` : "",
    rankingText ? `${rankingText}。` : "",
    experienceCount > 0 ? `已沉淀${experienceCount}段项目/实践经历，可支撑岗位匹配度表达。` : "当前项目与实践经历较少，建议重点突出课程基础、获奖与综合素质。",
    interestsText ? `兴趣方向：${interestsText}。` : "",
    knowledgeSummary ? `知识库参考：${knowledgeSummary}` : ""
  ].filter(Boolean);

  return {
    personalInfo: {
      name: input.name || "",
      gender: input.gender || "",
      phone: input.phone || "",
      email: input.email || "",
      university: input.school || "",
      politicalStatus: input.politicalStatus || "",
      website: input.website || "",
      avatar: "",
      major: input.major || "",
      applicationPosition: input.applicationPosition || input.targetRole || "",
      age: input.age || ""
    },
    education: educationItems.length ? educationItems : [{
      id: 1,
      school: input.school || "",
      degree: input.degree || "",
      major: input.major || "",
      startDate: "",
      endDate: ""
    }],
    workExperience: workItems,
    skills: skillItems,
    projects: projectItems,
    honors: honorItems,
    summary: summaryParts.join("\n")
  };
}

export async function generateResumePayload(input, template, references) {
  const llmResult = await callOpenAICompatibleModel(input, template, references);
  const resumeData = llmResult || generateLocalResume(input, template, references);

  return {
    resumeData,
    meta: {
      provider: llmResult ? "llm" : "local-fallback",
      templateId: template.id,
      templateName: template.name,
      knowledgeHits: references.map((item) => ({
        documentId: item.documentId,
        documentName: item.documentName,
        category: item.category,
        score: Number(item.score.toFixed(4))
      }))
    }
  };
}
