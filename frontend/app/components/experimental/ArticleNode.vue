<script setup lang="ts">
import { Handle, Position, useVueFlow } from '@vue-flow/core'
import type { ArticleNodeData } from '~/composables/useExperimentalGraph'

const props = defineProps<{
  id: string
  data: ArticleNodeData
}>()

const { updateNodeInternals } = useVueFlow()

watch(
  () => props.data.expanded,
  async () => {
    await nextTick()
    updateNodeInternals([props.id])
  }
)

function onFooterClick(event: MouseEvent) {
  event.stopPropagation()
  props.data.onToggleExpand()
}
</script>

<template>
  <div
    class="relative rounded-lg border bg-default shadow-sm flex flex-col transition-[width] duration-300"
    :class="[
      data.expanded ? 'w-150' : 'w-85',
      data.selected || data.highlighted
        ? 'border-primary ring-2 ring-primary/30'
        : 'border-default',
      data.expanded ? 'shadow-lg' : ''
    ]"
  >
    <Handle
      id="left"
      type="source"
      :position="Position.Left"
      class="size-2! bg-primary/40! border-0!"
    />
    <Handle
      id="right"
      type="source"
      :position="Position.Right"
      class="size-2! bg-primary/40! border-0!"
    />

    <div class="p-4 pb-3 cursor-pointer">
      <p class="text-[10px] font-bold uppercase tracking-wide text-primary">
        {{ data.sectionNumber ? `Artículo ${data.sectionNumber}` : 'Artículo' }}
      </p>
      <p
        class="mt-2 text-sm text-default leading-relaxed whitespace-pre-wrap"
        :class="data.expanded ? '' : 'line-clamp-4'"
      >
        {{ data.text }}
      </p>
    </div>

    <button
      type="button"
      class="mt-auto border-t border-default px-4 py-2 flex items-center justify-between gap-2 text-left cursor-pointer hover:bg-elevated/60 transition-colors rounded-b-lg"
      :aria-expanded="data.expanded"
      @click="onFooterClick"
      @mousedown.stop
      @pointerdown.stop
    >
      <span class="text-[11px] text-muted">
        {{ data.linkCount === 1 ? '1 vinculación' : `${data.linkCount} vinculaciones` }}
      </span>
      <span class="text-[11px] text-primary shrink-0">
        {{ data.expanded ? 'Contraer' : 'Expandir' }}
      </span>
    </button>
  </div>
</template>
