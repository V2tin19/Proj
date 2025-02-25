import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Template } from "../types/template";


export const useTemplateStore = defineStore('templateStore', () => {
  const currentTemplate = ref<Template | null>(null)
  const themeColor = ref<string>('#203CCB')  // 默认
  return { currentTemplate, themeColor }
}, {
  persist: true // 开启持久化存储
})
