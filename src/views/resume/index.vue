<template>
  <div class="resume">
    <div class="left">
      <div class="btn-group">
        <a-popconfirm
          title="填充会覆盖当前数据，确定吗？"
          ok-text="确定"
          cancel-text="取消"
          @confirm="resumeStore.autoFillData"
        >
          <template #icon><question-circle-outlined style="color: red" /></template>
          <a-button type="primary" ghost>
            <eye-outlined />
            预览填充
          </a-button>
        </a-popconfirm>

        <a-popconfirm
          title="确定要清空当前简历数据吗？"
          ok-text="清空"
          cancel-text="取消"
          @confirm="resumeStore.clearData"
        >
          <template #icon><warning-outlined style="color: red" /></template>
          <a-button danger>
            <delete-outlined />
            清空数据
          </a-button>
        </a-popconfirm>

        <a-button type="default" @click="resumeStore.exportData">
          <download-outlined />
          导出JSON
        </a-button>

        <a-upload
          v-model:fileList="fileList"
          :beforeUpload="handleFileUpload"
          :showUploadList="false"
          accept="application/json"
        >
          <a-button type="dashed">
            <upload-outlined />
            导入JSON
          </a-button>
        </a-upload>
      </div>

      <resumeEdit />
    </div>

    <div class="right">
      <resumePreview />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { message } from "ant-design-vue";
import type { UploadProps } from "ant-design-vue";
import resumeEdit from './components/resumeEdit.vue';
import resumePreview from './components/resumePreview.vue';
import { useResumeStore } from "../../store/useResumeStore";

const resumeStore = useResumeStore();
const fileList = ref<UploadProps["fileList"]>([]);

const handleFileUpload = (file: File) => {
  if (file.type !== "application/json") {
    message.error("请上传 JSON 文件！");
    return false;
  }

  resumeStore.importData(file);
  fileList.value = [];
  return false;
};
</script>

<style scoped>
.resume {
  display: flex;
  justify-content: space-between;
  height: calc(100vh - 60px);
  overflow: hidden;
}

.left {
  width: 38%;
  height: 100%;
  background:
    linear-gradient(180deg, rgba(7, 11, 18, 0.98), rgba(10, 17, 27, 0.98));
  border-right: 1px solid var(--border-color);
  transition: all 0.3s;
  min-width: 520px;
  display: flex;
  flex-direction: column;
}

.right {
  width: 62%;
  height: 100%;
  position: relative;
  overflow-y: auto;
  background: var(--bg-color);
}

.btn-group {
  height: 50px;
  display: flex;
  justify-content: center;
  gap: 20px;
  align-items: center;
  background: rgba(7, 11, 18, 0.86);
  border-bottom: 1px solid var(--border-color);
  backdrop-filter: blur(16px);
  flex-shrink: 0;
}

:deep(.resume-edit) {
  flex: 1;
  overflow-y: auto;
}
</style>
