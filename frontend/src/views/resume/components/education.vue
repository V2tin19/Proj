<template>
  <a-collapse class="education-collapse">
    <a-collapse-panel key="1" header="教育经历">
      <a-space direction="vertical" style="width: 100%">
        <!-- 教育经历列表 -->
        <div
          v-for="(edu, index) in education"
          :key="edu.id"
          class="education-item"
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
              aria-label="拖拽调整教育经历顺序"
              @dragstart="onDragStart(index, $event)"
              @dragend="onDragEnd"
            >
              <MenuOutlined />
            </button>
            <h4>教育经历 #{{ index + 1 }}</h4>
            <a-popconfirm title="确定要删除当前教育经历？" ok-text="删除" cancel-text="取消" @confirm="removeEducation(edu.id)">
              <template #icon><question-circle-outlined style="color: red" /></template>
              <a-button type="link" danger>删除</a-button>
            </a-popconfirm>
          </div>

          <a-form layout="vertical">
            <a-row gutter="24">
              <a-col :span="12">
                <a-input v-model:value="edu.school" placeholder="请输入学校名称" addonBefore="学校" />
              </a-col>
              <a-col :span="12">
                <a-input v-model:value="edu.major" placeholder="请输入专业" addonBefore="专业" />
              </a-col>
            </a-row>

            <a-row gutter="24" style="margin-top: 16px">
              <a-col :span="12">
                <a-date-picker v-model:value="edu.startDate" placeholder="开始时间" style="width: 100%" format="YYYY-MM-DD"
                  value-format="YYYY-MM-DD" />
              </a-col>
              <a-col :span="12">
                <a-date-picker v-model:value="edu.endDate" placeholder="结束时间" style="width: 100%" format="YYYY-MM-DD"
                  value-format="YYYY-MM-DD" />
              </a-col>
            </a-row>

            <a-input v-model:value="edu.degree" placeholder="请输入学位" addonBefore="学位" style="margin-top: 16px" />
          </a-form>
          <a-divider v-if="index !== education.length - 1" />
        </div>

        <!-- 添加按钮 -->
        <a-button type="dashed" block @click="addEducation" style="margin-top: 16px">
          <plus-outlined /> 添加教育经历
        </a-button>
      </a-space>
    </a-collapse-panel>
  </a-collapse>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { PlusOutlined, MenuOutlined } from '@ant-design/icons-vue';
import { useResumeStore } from '../../../store';
import { useDragReorder } from '../../../composables/useDragReorder';
import { QuestionCircleOutlined } from '@ant-design/icons-vue';
import { message } from 'ant-design-vue';

const resumeStore = useResumeStore();
const education = computed(() => resumeStore.education);
const { dragOverIndex, onDragStart, onDragEnd, onDragEnter, onDragLeave, onDragOver, onDrop } =
  useDragReorder(() => education.value, () => resumeStore.saveToLocalStorage());

// 添加教育经历
const addEducation = () => {
  resumeStore.addEducation({
    school: '',
    degree: '',
    major: '',
    startDate: '',
    endDate: ''
  });
};

// 删除教育经历
const removeEducation = (id: number) => {
  resumeStore.deleteEducation(id)
  message.success('教育经历删除成功！');
};
</script>

<style scoped>
.education-collapse {
  margin: 20px auto 0;
  max-width: 800px;
  font-family: 'zql';
  background-color: var(--panel-surface);
}

.education-item {
  width: 100%;
  position: relative;
  border-radius: 8px;
}

.item-header {
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.item-header h4 {
  margin: 0;
}

.item-header > :last-child {
  justify-self: end;
}

.item-drag-handle {
  width: 24px;
  height: 24px;
  display: inline-flex;
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

.education-item.is-drag-over {
  outline: 2px dashed #1677ff;
}
</style>
