<script setup lang="ts">
import { defineProps, computed, ref } from "vue";
import { sendToQwenAIDialogue } from "../../../api/qwenAPI";
import { useResumeStore } from "../../../store";
import type { AIDialogue, DialogueHistory } from "../../../types/aiDialogue";
import { defineEmits } from "vue";

const resumeStore = useResumeStore();
const personalInfo = computed(() => resumeStore.personalInfo);
const props = defineProps({
  description: String,
  extend: String
});

const emit = defineEmits<{
  update: [content: string]
}>();

const AIReply = ref("");
const loading = ref(false);
const AIextent = ref(false);
const canApply = computed(() => {
  return !!AIReply.value && AIReply.value.trim().length > 0;
});

const showTitle = computed(() => {
  if (!props.description || props.description.length < 5) {
    return "请输入更多信息后可使用 AI 功能";
  }
  return "AI 润色";
});

// 构建 AI 提示语
const buildPrompt = (text: string) => {
  return `我现在求职的 ${personalInfo.value.applicationPosition} 岗位。\n${text}`;
};

// 发送给 AI 处理
const handleAiEnhance = async (Prompt: string, isExtend: boolean) => {
  if (!Prompt || Prompt.length < 5) return;
  let message: AIDialogue = {
    role: "user",
    content: buildPrompt(Prompt)
  };
  let messages: DialogueHistory = [message];
  AIextent.value = isExtend;
  loading.value = true;
  AIReply.value = "";
  try {
    await sendToQwenAIDialogue(
      messages,
      (text, isComplete) => {
        AIReply.value = text;
        if (isComplete) {
          loading.value = false;
        }
      }
    );
  } catch (error) {
    console.error("AI 处理失败:", error);
    AIReply.value = "AI 处理失败，请稍后再试。";
    loading.value = false;
  }
};
const handleApply = () => {
  const content = AIReply.value.trim();
  if (content) {
    emit('update', content);
  }
};
</script>

<template>
  <a-popover :title="showTitle" trigger="click" placement="right" arrowPointAtCenter="true">
    <template #content v-if="description && description.length > 4">
      <div class="ai-controls">
        <a-button type="primary" @click="handleAiEnhance(description, false)" :loading="loading && !AIextent"
          :disabled="loading && AIextent">
          AI 润色
        </a-button>
        <a-button type="primary" @click="extend && handleAiEnhance(extend, true)" :loading="loading && AIextent"
          :disabled="loading && !AIextent">扩展方向</a-button>
      </div>

      <div class="ai-content">
        <a-spin :spinning="loading">
          <div v-if="AIReply" class="ai-editor">
            <a-textarea v-model:value="AIReply" :auto-size="{ minRows: 4, maxRows: 10 }" :disabled="loading" />
            <div v-if="!AIextent" class="apply-actions">
              <a-button type="link" size="small" @click="handleApply" :disabled="!canApply || loading">
                应用
              </a-button>
            </div>
          </div>
        </a-spin>
      </div>
    </template>
    <slot />
  </a-popover>
</template>

<style scoped>
.ai-controls {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}

.ai-content {
  min-width: 300px;
  max-width: 500px;
}

.ai-editor {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.apply-actions {
  display: flex;
  justify-content: flex-end;
}
</style>
