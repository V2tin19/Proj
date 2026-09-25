import { ref } from "vue";
import { moveItem } from "@/utils/reorder";

/**
 * 列表拖拽排序逻辑(编辑页各分区共用)。
 * 之前这段 ~60 行的处理函数在 5 个分区组件里逐字复制,现收敛为一处。
 *
 * @param getList     当前列表(响应式 getter)
 * @param onReordered 排序发生后的回调(如持久化)
 */
export function useDragReorder<T>(getList: () => T[], onReordered?: () => void) {
  const draggingIndex = ref<number | null>(null);
  const dragOverIndex = ref<number | null>(null);

  const onDragStart = (index: number, event: DragEvent) => {
    draggingIndex.value = index;
    dragOverIndex.value = null;
    event.dataTransfer?.setData("text/plain", String(index));
    if (event.dataTransfer) {
      event.dataTransfer.effectAllowed = "move";
    }
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
    if (event.dataTransfer) {
      event.dataTransfer.dropEffect = "move";
    }
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
      moveItem(getList(), fromIndex, toIndex);
      onReordered?.();
    }
    draggingIndex.value = null;
    dragOverIndex.value = null;
  };

  return {
    draggingIndex,
    dragOverIndex,
    onDragStart,
    onDragEnd,
    onDragEnter,
    onDragLeave,
    onDragOver,
    onDrop,
  };
}
