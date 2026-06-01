<template>
  <div class="resume">
    <div class="mobile-view-tabs">
      <a-segmented
        v-model:value="mobilePane"
        :options="[
          { label: '编辑', value: 'edit' },
          { label: '预览', value: 'preview' }
        ]"
        block
      />
    </div>

    <div class="left" :class="{ 'is-mobile-hidden': mobilePane !== 'edit' }">
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

    <div class="right" :class="{ 'is-mobile-hidden': mobilePane !== 'preview' }">
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
const mobilePane = ref<'edit' | 'preview'>('edit');

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

.mobile-view-tabs {
  display: none;
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

@media (max-width: 768px) {
  .resume {
    display: block;
    height: auto;
    min-height: 100svh;
    overflow: visible;
    padding: 12px;
  }

  .mobile-view-tabs {
    display: block;
    position: sticky;
    top: 0;
    z-index: 20;
    padding-bottom: 10px;
    background: linear-gradient(180deg, rgba(7, 11, 18, 0.98), rgba(7, 11, 18, 0.72));
    backdrop-filter: blur(12px);
  }

  .left,
  .right {
    width: 100%;
    min-width: 0;
    height: calc(100svh - 148px);
    min-height: 520px;
    border: 1px solid var(--border-color);
    border-radius: 14px;
    overflow: hidden;
  }

  .left {
    display: flex;
    border-right: 1px solid var(--border-color);
  }

  .right {
    display: block;
  }

  .is-mobile-hidden {
    display: none !important;
  }

  .btn-group {
    height: auto;
    min-height: 58px;
    justify-content: flex-start;
    gap: 8px;
    padding: 9px;
    overflow-x: auto;
  }

  .btn-group :deep(.ant-btn) {
    min-height: 38px;
    padding: 0 12px;
    white-space: nowrap;
  }

  :deep(.resume-edit) {
    min-height: 0;
  }

  :deep(.ant-row) {
    margin-left: 0 !important;
    margin-right: 0 !important;
    row-gap: 12px;
  }

  :deep(.ant-col) {
    flex: 0 0 100% !important;
    max-width: 100% !important;
    padding-left: 0 !important;
    padding-right: 0 !important;
  }

  :deep(.ant-input),
  :deep(.ant-input-affix-wrapper),
  :deep(.ant-select-selector),
  :deep(.ant-picker),
  :deep(.ant-input-number) {
    min-height: 42px;
  }

  :deep(.ant-input-group-addon) {
    white-space: nowrap;
  }
}
</style>
