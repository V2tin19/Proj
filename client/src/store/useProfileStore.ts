/**
 * 简历档案 store:多套简历的保存 / 切换 / 管理。
 *
 * 存储分两层,按登录态自动选择:
 * - local:整表存 localStorage(匿名模式)
 * - cloud:登录后以服务端 /api/profiles 为准,编辑防抖 PUT 保存
 * 登录时本机档案一次性上传合并(onLoginSuccess),之后云端为唯一事实源。
 *
 * 档案快照 = 7 个内容分区 + sectionOrder + resumeSetting + agentConfig,
 * 编辑态始终在 useResumeStore,本 store 只负责"当前编辑的是哪份档案"。
 */
import { defineStore } from 'pinia';
import { computed, ref } from 'vue';
import { message } from 'ant-design-vue';
import { useResumeStore } from './useResumeStore';
import {
  createProfile as apiCreate,
  fetchProfile as apiFetch,
  listProfiles as apiList,
  removeProfile as apiRemove,
  updateProfile as apiUpdate
} from '../api/agentAPI';
import { hasSession } from '../utils/auth';
import type { ProfileMeta, ProfileSnapshot } from '../types/profile';

export type ProfileScope = 'local' | 'cloud';
export type SaveState = 'idle' | 'saving' | 'saved' | 'error';

interface StoredProfile extends ProfileMeta {
  data: ProfileSnapshot;
}

const LS_LOCAL_TABLE = 'resumeProfiles'; // { profiles: StoredProfile[], activeProfileId }
const LS_CLOUD_ACTIVE = 'cloudActiveProfile';
const LS_SYNC_FLAG_PREFIX = 'profilesCloudSynced.';
const SAVE_DEBOUNCE_MS = 800;

function newLocalId(): string {
  return `prof-local-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
}

function readLocalTable(): { profiles: StoredProfile[]; activeProfileId: string | null } | null {
  try {
    const raw = localStorage.getItem(LS_LOCAL_TABLE);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed?.profiles)) return null;
    return { profiles: parsed.profiles, activeProfileId: parsed.activeProfileId ?? null };
  } catch {
    return null;
  }
}

function writeLocalTable(profiles: StoredProfile[], activeProfileId: string | null) {
  localStorage.setItem(LS_LOCAL_TABLE, JSON.stringify({ profiles, activeProfileId }));
}

export const useProfileStore = defineStore('profile', () => {
  const resumeStore = useResumeStore();

  const profiles = ref<ProfileMeta[]>([]);
  const activeProfileId = ref<string | null>(null);
  const scope = ref<ProfileScope>('local');
  const saveState = ref<SaveState>('idle');
  const lastSavedAt = ref<string | null>(null);
  const loading = ref(false);

  let initializedScope: ProfileScope | null = null;
  let localTable: { profiles: StoredProfile[]; activeProfileId: string | null } | null = null;
  let debounceTimer: ReturnType<typeof setTimeout> | null = null;
  let inflightSave: Promise<void> | null = null;
  let suppressSave = false;
  let subscribed = false;

  function subscribeEdits() {
    if (subscribed) return;
    subscribed = true;
    // 任何编辑(agent 页改策略、编辑页改内容)都防抖写回当前档案
    resumeStore.$subscribe(() => schedulePersist());
  }

  const activeProfile = computed(
    () => profiles.value.find((item) => item.id === activeProfileId.value) ?? null
  );
  const activeProfileName = computed(() => activeProfile.value?.name ?? '未命名档案');

  // ------------------------------------------------------------ 快照

  function snapshotCurrent(): ProfileSnapshot {
    const state = resumeStore.$state;
    return {
      personalInfo: state.personalInfo,
      education: state.education,
      workExperience: state.workExperience,
      skills: state.skills,
      projects: state.projects,
      honors: state.honors,
      summary: state.summary,
      sectionOrder: state.sectionOrder,
      resumeSetting: state.resumeSetting,
      agentConfig: state.agentConfig
    };
  }

  // ------------------------------------------------------------ 保存(防抖)

  function persistActiveNow(): Promise<void> {
    if (!activeProfileId.value) return Promise.resolve();
    const snapshot = snapshotCurrent();

    if (scope.value === 'local') {
      const entry = localTable?.profiles.find((item) => item.id === activeProfileId.value);
      if (entry) {
        entry.data = snapshot;
        entry.updatedAt = new Date().toISOString();
        if (localTable) writeLocalTable(localTable.profiles, localTable.activeProfileId);
      }
      saveState.value = 'saved';
      lastSavedAt.value = new Date().toISOString();
      return Promise.resolve();
    }

    saveState.value = 'saving';
    const job = (inflightSave ?? Promise.resolve()).then(async () => {
      await apiUpdate(activeProfileId.value as string, { data: snapshot });
      saveState.value = 'saved';
      lastSavedAt.value = new Date().toISOString();
      const meta = profiles.value.find((item) => item.id === activeProfileId.value);
      if (meta) meta.updatedAt = new Date().toISOString();
    }).catch(() => {
      saveState.value = 'error';
    }).finally(() => {
      if (inflightSave === job) inflightSave = null;
    });
    inflightSave = job;
    return job;
  }

  function schedulePersist() {
    if (suppressSave || !activeProfileId.value) return;
    saveState.value = 'saving';
    if (debounceTimer) clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
      debounceTimer = null;
      persistActiveNow();
    }, SAVE_DEBOUNCE_MS);
  }

  async function flushSave(): Promise<void> {
    if (debounceTimer) {
      clearTimeout(debounceTimer);
      debounceTimer = null;
    }
    await (inflightSave ?? Promise.resolve());
    await persistActiveNow();
  }

  // ------------------------------------------------------------ 初始化

  /** 幂等初始化;登录态变化后再次调用会按新 scope 重建 */
  async function ensureReady(): Promise<void> {
    const targetScope: ProfileScope = hasSession() ? 'cloud' : 'local';
    if (initializedScope === targetScope) return;
    initializedScope = targetScope;
    scope.value = targetScope;
    loading.value = true;
    try {
      if (targetScope === 'local') {
        await initLocal();
      } else {
        await initCloud();
      }
      subscribeEdits();
    } finally {
      loading.value = false;
    }
  }

  async function initLocal() {
    localTable = readLocalTable();
    if (!localTable || localTable.profiles.length === 0) {
      // 首次使用:把现有单份简历迁移为"默认档案"
      const now = new Date().toISOString();
      const entry: StoredProfile = {
        id: newLocalId(),
        name: '默认档案',
        remark: '',
        data: snapshotCurrent(),
        createdAt: now,
        updatedAt: now
      };
      localTable = { profiles: [entry], activeProfileId: entry.id };
    } else {
      // 引导时 resumeStore 从旧缓存 resumeData 启动,以编辑器现状回写当前档案
      const active = localTable.profiles.find(
        (item) => item.id === localTable?.activeProfileId
      );
      if (active) active.data = snapshotCurrent();
      if (!active) {
        localTable.activeProfileId = localTable.profiles[0]?.id ?? null;
      }
    }
    profiles.value = localTable.profiles.map(({ data: _data, ...meta }) => meta);
    activeProfileId.value = localTable.activeProfileId;
    writeLocalTable(localTable.profiles, localTable.activeProfileId);
  }

  async function initCloud() {
    let metas: ProfileMeta[];
    try {
      metas = await apiList();
    } catch {
      // 云端不可达:退回本地模式展示,下次挂载/登录再试
      initializedScope = 'local';
      scope.value = 'local';
      await initLocal();
      return;
    }

    if (metas.length === 0) {
      const created = await apiCreate({
        name: readLocalTable()?.profiles.find(
          (item) => item.id === readLocalTable()?.activeProfileId
        )?.name || '默认档案',
        data: snapshotCurrent()
      });
      metas = [{ id: created.id, name: created.name, remark: created.remark,
        createdAt: created.createdAt, updatedAt: created.updatedAt }];
    }

    profiles.value = metas;
    const remembered = localStorage.getItem(LS_CLOUD_ACTIVE);
    const active = (metas.some((item) => item.id === remembered) ? remembered : null) ?? metas[0].id;
    activeProfileId.value = active;
    localStorage.setItem(LS_CLOUD_ACTIVE, active);

    suppressSave = true;
    try {
      const detail = await apiFetch(active);
      resumeStore.applyProfile(detail.data);
    } catch (error) {
      console.error('载入云端档案失败', error);
      message.warning('云端档案载入失败,当前显示本机内容');
    } finally {
      setTimeout(() => { suppressSave = false; }, 100);
    }
  }

  // ------------------------------------------------------------ 档案操作

  async function switchProfile(id: string): Promise<void> {
    if (id === activeProfileId.value) return;
    await ensureReady();
    await flushSave();
    loading.value = true;
    suppressSave = true;
    try {
      if (scope.value === 'local') {
        const entry = localTable?.profiles.find((item) => item.id === id);
        if (!entry) throw new Error('档案不存在');
        resumeStore.applyProfile(entry.data);
        activeProfileId.value = id;
        if (localTable) {
          localTable.activeProfileId = id;
          writeLocalTable(localTable.profiles, id);
        }
      } else {
        const detail = await apiFetch(id);
        resumeStore.applyProfile(detail.data);
        activeProfileId.value = id;
        profiles.value = profiles.value.map((item) =>
          item.id === id ? { ...item, updatedAt: detail.updatedAt } : item
        );
        localStorage.setItem(LS_CLOUD_ACTIVE, id);
      }
      saveState.value = 'idle';
      message.success(`已切换到「${activeProfile.value?.name ?? ''}」`);
    } catch (error) {
      console.error(error);
      message.error((error as Error).message || '档案切换失败');
    } finally {
      setTimeout(() => { suppressSave = false; }, 100);
      loading.value = false;
    }
  }

  /** 把当前编辑内容另存为新档案并切换过去 */
  async function saveAsNew(name: string, remark = ''): Promise<boolean> {
    await ensureReady();
    const data = snapshotCurrent();
    try {
      if (scope.value === 'local') {
        const now = new Date().toISOString();
        const entry: StoredProfile = { id: newLocalId(), name, remark, data, createdAt: now, updatedAt: now };
        localTable?.profiles.push(entry);
        if (localTable) {
          localTable.activeProfileId = entry.id;
          writeLocalTable(localTable.profiles, entry.id);
        }
        profiles.value = [...(profiles.value), { id: entry.id, name, remark, createdAt: now, updatedAt: now }];
        activeProfileId.value = entry.id;
      } else {
        const created = await apiCreate({ name, remark, data });
        profiles.value = [{ id: created.id, name: created.name, remark: created.remark,
          createdAt: created.createdAt, updatedAt: created.updatedAt }, ...profiles.value];
        activeProfileId.value = created.id;
        localStorage.setItem(LS_CLOUD_ACTIVE, created.id);
      }
      saveState.value = 'saved';
      message.success(`已保存为新档案「${name}」`);
      return true;
    } catch (error) {
      console.error(error);
      message.error((error as Error).message || '保存档案失败');
      return false;
    }
  }

  /** 新建空白档案(模板默认内容)并切换 */
  async function createBlank(name: string): Promise<void> {
    await ensureReady();
    suppressSave = true;
    // 先把编辑器重置为空白模板,再走"另存为"路径
    resumeStore.clearData();
    setTimeout(() => { suppressSave = false; }, 100);
    await saveAsNew(name || '空白档案');
  }

  async function renameProfile(id: string, name: string): Promise<void> {
    await ensureReady();
    try {
      if (scope.value === 'local') {
        const entry = localTable?.profiles.find((item) => item.id === id);
        if (entry) {
          entry.name = name;
          if (localTable) writeLocalTable(localTable.profiles, localTable.activeProfileId);
        }
      } else {
        await apiUpdate(id, { name });
      }
      profiles.value = profiles.value.map((item) => (item.id === id ? { ...item, name } : item));
      message.success('已重命名');
    } catch (error) {
      console.error(error);
      message.error((error as Error).message || '重命名失败');
    }
  }

  async function duplicateProfile(id: string): Promise<void> {
    await ensureReady();
    try {
      const source = scope.value === 'local'
        ? localTable?.profiles.find((item) => item.id === id)
        : await apiFetch(id);
      if (!source) throw new Error('档案不存在');
      await saveAsNew(`${source.name} 副本`, source.remark);
      if (scope.value === 'cloud') {
        // saveAsNew 保存的是"当前编辑内容";复制他人档案需再写入源数据
        await apiUpdate(activeProfileId.value as string, { data: source.data });
        resumeStore.applyProfile(source.data);
      } else if (localTable) {
        const entry = localTable.profiles.find((item) => item.id === activeProfileId.value);
        if (entry) {
          entry.data = source.data;
          resumeStore.applyProfile(source.data);
          writeLocalTable(localTable.profiles, localTable.activeProfileId);
        }
      }
    } catch (error) {
      console.error(error);
      message.error((error as Error).message || '复制档案失败');
    }
  }

  async function removeProfile(id: string): Promise<void> {
    await ensureReady();
    try {
      if (scope.value === 'local') {
        if (localTable) {
          localTable.profiles = localTable.profiles.filter((item) => item.id !== id);
          if (localTable.activeProfileId === id) {
            const fallback = localTable.profiles[0] ?? null;
            localTable.activeProfileId = fallback?.id ?? null;
            activeProfileId.value = fallback?.id ?? null;
            if (fallback) resumeStore.applyProfile(fallback.data);
          }
          writeLocalTable(localTable.profiles, localTable.activeProfileId);
        }
      } else {
        await apiRemove(id);
        profiles.value = profiles.value.filter((item) => item.id !== id);
        if (activeProfileId.value === id) {
          const fallback = profiles.value[0] ?? null;
          if (fallback) {
            await switchProfile(fallback.id);
          } else {
            activeProfileId.value = null;
          }
        }
      }
      message.success('档案已删除');
    } catch (error) {
      console.error(error);
      message.error((error as Error).message || '删除失败');
    }
  }

  // ------------------------------------------------------------ 登录同步

  /** 登录成功后调用:本机档案一次性上传合并,云端此后为唯一事实源 */
  async function onLoginSuccess(username: string): Promise<void> {
    const flagKey = LS_SYNC_FLAG_PREFIX + username;
    const table = readLocalTable();
    try {
      if (table && table.profiles.length > 0 && localStorage.getItem(flagKey) !== '1') {
        let activeMappedId: string | null = null;
        for (const entry of table.profiles) {
          try {
            const created = await apiCreate({ name: entry.name, remark: entry.remark, data: entry.data });
            if (entry.id === table.activeProfileId) activeMappedId = created.id;
          } catch {
            // 重名等服务端校验冲突时加后缀重试一次
            try {
              const created = await apiCreate({
                name: `${entry.name}(本机)`, remark: entry.remark, data: entry.data
              });
              if (entry.id === table.activeProfileId) activeMappedId = created.id;
            } catch (inner) {
              console.error('本机档案上传失败', inner);
            }
          }
        }
        if (activeMappedId) localStorage.setItem(LS_CLOUD_ACTIVE, activeMappedId);
        localStorage.setItem(flagKey, '1');
        if (table.profiles.length > 0) {
          message.success(`已将 ${table.profiles.length} 份本机档案同步到云端`);
        }
      }
    } catch (error) {
      console.error('本机档案云端合并失败(不影响使用)', error);
    }
    initializedScope = null;
    await ensureReady();
  }

  return {
    profiles,
    activeProfileId,
    activeProfile,
    activeProfileName,
    scope,
    saveState,
    lastSavedAt,
    loading,
    ensureReady,
    switchProfile,
    saveAsNew,
    createBlank,
    renameProfile,
    duplicateProfile,
    removeProfile,
    flushSave,
    onLoginSuccess,
    _schedulePersist: schedulePersist
  };
});
