<template>
  <a-collapse class="skills-collapse">
    <a-collapse-panel key="1" header="专业技能">
      <a-space direction="vertical" style="width: 100%">
        <!-- 技能列表 -->
        <div
          v-for="(skill, index) in skills"
          :key="skill.id"
          class="skill-item"
          :class="{ 'is-drag-over': dragOverIndex === index }"
          @dragenter.prevent="onDragEnter(index)"
          @dragover.prevent="onDragOver(index, $event)"
          @dragleave="onDragLeave(index)"
          @drop="onDrop(index, $event)"
        >
          <div class="item-header">
            <button
              class="item-drag-handle"
              type="button"
              draggable="true"
              aria-label="拖拽调整技能顺序"
              @dragstart="onDragStart(index, $event)"
              @dragend="onDragEnd"
            >
              <MenuOutlined />
            </button>
            <h4>技能 #{{ index + 1 }}</h4>
            <a-popconfirm title="确定要删除当前技能？" ok-text="删除" cancel-text="取消" @confirm="removeSkill(skill.id)">
              <template #icon><question-circle-outlined style="color: red" /></template>
              <a-button type="link" danger>删除</a-button>
            </a-popconfirm>
          </div>

          <a-form layout="vertical">
            <AIEnhancePopover :description="`请帮我润色和优化以下内容，是我简历中的技能描述，
                    使其更加简洁、专业和吸引面试官，不要多余的文字说明：\n${skill.skillName}`" :extend="`下面这个是我简历中的技能描述，我可以从哪些方面扩展优化？你的回复用文本就行，不需要md语法，给我一些思路：
                    \n${skill.skillName}`" @update="(content: string) => skill.skillName = content">
              <a-input v-model:value="skill.skillName" placeholder="请输入技能名称" addonBefore="技能" />
            </AIEnhancePopover>


          </a-form>
          <a-divider v-if="index !== skills.length - 1" />
        </div>

        <!-- 添加按钮 -->
        <a-button type="dashed" block @click="addSkill" style="margin-top: 16px">
          <plus-outlined /> 添加技能
        </a-button>
      </a-space>
    </a-collapse-panel>
  </a-collapse>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { PlusOutlined, MenuOutlined } from '@ant-design/icons-vue';
import { useResumeStore } from '../../../store';
import { QuestionCircleOutlined } from '@ant-design/icons-vue';
import { message } from 'ant-design-vue';
import AIEnhancePopover from './AIEnhancePopover.vue';
import { moveItem } from '../../../utils/reorder';

const resumeStore = useResumeStore();
const skills = computed(() => resumeStore.skills);
const draggingIndex = ref<number | null>(null);
const dragOverIndex = ref<number | null>(null);

// 添加技能
const addSkill = () => {
  resumeStore.addSkill({
    skillName: ''
  });
};

// 删除技能
const removeSkill = (id: number) => {
  resumeStore.deleteSkill(id)
  message.success('技能删除成功！');
};

const onDragStart = (index: number, event: DragEvent) => {
  draggingIndex.value = index;
  dragOverIndex.value = null;
  event.dataTransfer?.setData('text/plain', String(index));
  event.dataTransfer && (event.dataTransfer.effectAllowed = 'move');
};

const onDragEnd = () => {
  draggingIndex.value = null;
  dragOverIndex.value = null;
};

const onDragEnter = (index: number) => {
  if (draggingIndex.value === null || draggingIndex.value === index) return;
  dragOverIndex.value = index;
};

const onDragLeave = (index: number) => {
  if (dragOverIndex.value === index) {
    dragOverIndex.value = null;
  }
};

const onDragOver = (index: number, event: DragEvent) => {
  if (draggingIndex.value === null) return;
  event.dataTransfer && (event.dataTransfer.dropEffect = 'move');
  if (dragOverIndex.value !== index && draggingIndex.value !== index) {
    dragOverIndex.value = index;
  }
};

const onDrop = (index: number, event: DragEvent) => {
  event.preventDefault();
  if (draggingIndex.value === null) return;
  const currentTarget = event.currentTarget as HTMLElement | null;
  let toIndex = index;
  if (currentTarget) {
    const rect = currentTarget.getBoundingClientRect();
    const offset = event.clientY - rect.top;
    if (offset > rect.height / 2) {
      toIndex = index + 1;
    }
  }
  const fromIndex = draggingIndex.value;
  if (fromIndex < toIndex) {
    toIndex -= 1;
  }
  if (fromIndex !== toIndex) {
    moveItem(skills.value, fromIndex, toIndex);
    resumeStore.saveToLocalStorage();
  }
  draggingIndex.value = null;
  dragOverIndex.value = null;
};

// 监听变化并保存到 localStorage
watch(
  () => resumeStore.$state,
  () => {
    resumeStore.saveToLocalStorage();
  },
  { deep: true }
);
</script>

<style scoped>
.skills-collapse {
  margin: 20px auto 0;
  max-width: 800px;
  font-family: 'zql';
  background-color: var(--color-7);
}

.skill-item {
  width: 100%;
  position: relative;
  padding-left: 28px;
  border-radius: 8px;
}

.item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.item-header h4 {
  margin: 0;
}

.item-drag-handle {
  position: absolute;
  left: 0;
  top: 16px;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: grab;
  border: none;
  background: transparent;
  color: #8c8c8c;
  padding: 0;
}

.item-drag-handle:active {
  cursor: grabbing;
}

.skill-item.is-drag-over {
  outline: 2px dashed #1677ff;
}
</style>