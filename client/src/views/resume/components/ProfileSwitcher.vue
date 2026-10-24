<template>
  <div class="profile-switcher">
    <a-dropdown :trigger="['click']">
      <a-button class="profile-trigger" :loading="store.loading">
        <folder-outlined />
        <span class="trigger-name">{{ store.activeProfileName }}</span>
        <span class="scope-tag" :class="store.scope">{{ store.scope === 'cloud' ? '云端' : '本机' }}</span>
        <down-outlined />
      </a-button>
      <template #overlay>
        <a-menu @click="onMenuClick">
          <a-menu-item
            v-for="item in store.profiles"
            :key="item.id"
            :class="{ 'is-active': item.id === store.activeProfileId }"
          >
            <check-outlined v-if="item.id === store.activeProfileId" />
            <span class="menu-name">{{ item.name }}</span>
            <span class="menu-time">{{ formatTime(item.updatedAt) }}</span>
          </a-menu-item>
          <a-menu-divider />
          <a-menu-item key="__saveas"><save-outlined /> 另存为新档案</a-menu-item>
          <a-menu-item key="__blank"><file-add-outlined /> 新建空白档案</a-menu-item>
          <a-menu-item key="__manage"><appstore-outlined /> 管理档案…</a-menu-item>
        </a-menu>
      </template>
    </a-dropdown>

    <span v-if="saveHint" class="save-hint">{{ saveHint }}</span>

    <a-modal
      v-model:open="nameModalOpen"
      :title="nameModalTitle"
      :ok-text="nameModalOkText"
      cancel-text="取消"
      @ok="confirmNameModal"
    >
      <a-input
        v-model:value="nameDraft"
        placeholder="档案名称，如：前端岗-张三"
        :maxlength="50"
        @press-enter="confirmNameModal"
      />
    </a-modal>

    <a-modal v-model:open="manageOpen" title="管理简历档案" :footer="null" :width="560">
      <p class="scope-hint">
        当前存储：{{ store.scope === 'cloud' ? '云端（随登录账号，多设备同步）' : '本机（浏览器本地，登录后可同步到云端）' }}
      </p>
      <div v-for="item in store.profiles" :key="item.id" class="manage-row">
        <div class="manage-info">
          <strong>{{ item.name }}</strong>
          <small>更新于 {{ formatTime(item.updatedAt) }}</small>
        </div>
        <a-space>
          <a-button size="small" @click="startRename(item)">重命名</a-button>
          <a-button size="small" @click="store.duplicateProfile(item.id)">复制</a-button>
          <a-popconfirm title="确定删除这份档案吗？" ok-text="删除" cancel-text="取消" @confirm="store.removeProfile(item.id)">
            <a-button size="small" danger ghost>删除</a-button>
          </a-popconfirm>
        </a-space>
      </div>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import {
  AppstoreOutlined, CheckOutlined, DownOutlined,
  FileAddOutlined, FolderOutlined, SaveOutlined
} from '@ant-design/icons-vue';
import { useProfileStore } from '../../../store/useProfileStore';
import type { ProfileMeta } from '../../../types/profile';

const store = useProfileStore();

onMounted(() => {
  store.ensureReady();
});

const saveHint = computed(() => {
  if (store.saveState === 'saving') return '保存中…';
  if (store.saveState === 'error') return '保存失败,稍后重试';
  return '';
});

function formatTime(iso: string): string {
  if (!iso) return '';
  return iso.slice(0, 16).replace('T', ' ');
}

// ---- 命名弹窗(另存为 / 新建空白 / 重命名 复用) ----
type NameMode = 'saveas' | 'blank' | { rename: string };
const nameModalOpen = ref(false);
const nameMode = ref<NameMode>('saveas');
const nameDraft = ref('');

const nameModalTitle = computed(() =>
  nameMode.value === 'blank' ? '新建空白档案' :
  nameMode.value === 'saveas' ? '另存为新档案' : '重命名档案'
);
const nameModalOkText = computed(() => (nameMode.value === 'saveas' ? '保存' : '确定'));

function openNameModal(mode: NameMode, initial = '') {
  nameMode.value = mode;
  nameDraft.value = initial;
  nameModalOpen.value = true;
}

async function confirmNameModal() {
  const name = nameDraft.value.trim();
  if (!name) return;
  nameModalOpen.value = false;
  const mode = nameMode.value;
  if (mode === 'saveas') {
    await store.saveAsNew(name);
  } else if (mode === 'blank') {
    await store.createBlank(name);
  } else {
    await store.renameProfile(mode.rename, name);
  }
}

function startRename(profile: ProfileMeta) {
  openNameModal({ rename: profile.id }, profile.name);
}

const manageOpen = ref(false);

function onMenuClick({ key }: { key: string | number }) {
  if (key === '__saveas') {
    openNameModal('saveas');
  } else if (key === '__blank') {
    openNameModal('blank');
  } else if (key === '__manage') {
    manageOpen.value = true;
  } else {
    store.switchProfile(String(key));
  }
}
</script>

<style scoped>
.profile-switcher {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.profile-trigger {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  max-width: 280px;
}

.trigger-name {
  max-width: 140px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.scope-tag {
  font-size: 11px;
  line-height: 1;
  padding: 3px 6px;
  border-radius: 4px;
  background: rgba(45, 91, 255, 0.12);
  color: var(--primary-color);
  flex-shrink: 0;
}

.scope-tag.cloud {
  background: rgba(82, 196, 26, 0.15);
  color: #389e0d;
}

.save-hint {
  font-size: 12px;
  color: var(--text-muted);
  white-space: nowrap;
}

.menu-name {
  margin-right: 10px;
}

.menu-time {
  color: var(--text-muted);
  font-size: 12px;
}

.is-active {
  font-weight: 600;
}

.scope-hint {
  font-size: 12px;
  color: var(--text-muted);
  margin: 0 0 12px;
}

.manage-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 12px;
  border: 1px solid var(--border-color);
  border-radius: 10px;
  margin-bottom: 10px;
  background: var(--inset-bg);
}

.manage-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.manage-info strong {
  color: var(--text-color);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.manage-info small {
  color: var(--text-muted);
  font-size: 12px;
}

@media (max-width: 768px) {
  .save-hint {
    display: none;
  }
}
</style>
