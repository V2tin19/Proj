import { computed, onMounted, watch } from "vue";
import { useResumeStore } from "@/store/useResumeStore";
import { normalizeSectionOrder } from "@/constants/sectionOrder";
import type { SectionKey } from "@/types/resume";

/**
 * 五套简历布局模板共享的取数与样式逻辑。
 * 模板组件只保留自己的布局 HTML/CSS,不复制脚本。
 */
export function useResumeStyle() {
  const resumeStore = useResumeStore();
  const resume = computed(() => resumeStore.$state);

  // 间距/版式变量(所有模板共用)
  const spacingStyle = computed(() => ({
    "--paragraph-spacing": `${resume.value.resumeSetting.paragraphSpacing}px`,
    "--section-spacing": `${resume.value.resumeSetting.sectionSpacing}px`,
    "--padding-left-right": `${resume.value.resumeSetting.padding_left_right}px`,
    "--padding-top-bottom": `${resume.value.resumeSetting.padding_top_bottom}px`,
  }));

  // 主题色变量(仅 templateA/B/C 使用;templateD/dev 通过 colorShades prop 取色)
  const themeColorStyle = computed(() => ({
    "--themeColor1": resume.value.resumeSetting.themeColor1,
    "--themeColor2": resume.value.resumeSetting.themeColor2,
  }));

  // 注入到模板根元素的 CSS 变量
  const resumeStyle = computed(() => ({
    ...spacingStyle.value,
    ...themeColorStyle.value,
  }));

  const sectionOrder = computed<SectionKey[]>(() =>
    normalizeSectionOrder(resume.value.sectionOrder)
  );

  const sectionStyle = (key: SectionKey, offset = 0) => {
    const index = sectionOrder.value.indexOf(key);
    const base = index === -1 ? sectionOrder.value.length : index;
    return { order: base + offset };
  };

  // 字号设置通过根元素 font-size 生效(模板内部使用 rem)。
  // 注意:这是全局副作用,同一时刻只有一个模板实例处于挂载状态,
  // 卸载后由下一个挂载实例接管,无需清理。
  const applyFontSize = (size: number) => {
    document.documentElement.style.fontSize = `${size}px`;
  };

  onMounted(() => applyFontSize(resume.value.resumeSetting.fontSize));
  watch(
    () => resume.value.resumeSetting.fontSize,
    (newSize) => applyFontSize(newSize)
  );

  return { resume, resumeStore, resumeStyle, spacingStyle, sectionOrder, sectionStyle };
}
