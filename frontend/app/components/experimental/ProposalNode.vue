<script setup lang="ts">
import { Handle, Position, useVueFlow } from '@vue-flow/core'
import type { ProposalNodeData } from '~/composables/useExperimentalGraph'

const props = defineProps<{
  id: string
  data: ProposalNodeData
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

/** Keep wheel scrolling inside the node; don't zoom the canvas. */
function onBodyWheel(event: WheelEvent) {
  if (!props.data.expanded) return
  event.stopPropagation()
}
</script>

<template>
  <div
    class="relative rounded-lg border bg-default shadow-sm flex flex-col transition-[width] duration-300"
    :class="[
      data.expanded ? 'w-150' : 'w-85',
      data.selected || data.highlighted
        ? 'border-warning ring-2 ring-warning/25'
        : 'border-default',
      data.expanded ? 'shadow-lg' : ''
    ]"
  >
    <Handle
      id="left"
      type="target"
      :position="Position.Left"
      class="size-2! bg-warning/40! border-0!"
    />
    <Handle
      id="right"
      type="target"
      :position="Position.Right"
      class="size-2! bg-warning/40! border-0!"
    />

    <div
      class="flex min-w-0 flex-1 cursor-pointer"
      :class="data.expanded ? 'max-h-96 overflow-y-auto overscroll-contain nowheel' : ''"
      @wheel="onBodyWheel"
    >
      <div class="w-1 shrink-0 bg-warning self-stretch" />
      <div class="p-4 pb-3 min-w-0 flex-1">
        <p class="text-[10px] font-bold uppercase tracking-wide text-warning">
          Propuesta #{{ data.proposalId }}
        </p>
        <p
          class="mt-2 text-sm text-default leading-relaxed whitespace-pre-wrap"
          :class="data.expanded ? '' : 'line-clamp-4'"
        >
          {{ data.text }}
        </p>
      </div>
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
        {{ data.linkCount === 1 ? '1 artículo' : `${data.linkCount} artículos` }}
      </span>
      <span class="text-[11px] text-warning shrink-0">
        {{ data.expanded ? 'Contraer' : 'Expandir' }}
      </span>
    </button>
  </div>
</template>
