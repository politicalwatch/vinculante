<script setup lang="ts">
import { Handle, Position } from '@vue-flow/core'
import type { ProposalNodeData } from '~/composables/useExperimentalGraph'

defineProps<{
  data: ProposalNodeData
}>()
</script>

<template>
  <div
    class="relative w-85 rounded-lg border bg-default shadow-sm flex flex-col cursor-pointer transition-shadow"
    :class="data.selected || data.highlighted
      ? 'border-warning ring-2 ring-warning/25'
      : 'border-default'"
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

    <div class="flex min-w-0 flex-1">
      <div class="w-1 shrink-0 bg-warning self-stretch" />
      <div class="p-4 pb-3 min-w-0 flex-1">
        <p class="text-[10px] font-bold uppercase tracking-wide text-warning">
          Propuesta #{{ data.proposalId }}
        </p>
        <p class="mt-2 text-sm text-default leading-relaxed line-clamp-4">
          {{ data.text }}
        </p>
      </div>
    </div>

    <div class="mt-auto border-t border-default px-4 py-2">
      <span class="text-[11px] text-muted">
        {{ data.linkCount === 1 ? '1 artículo' : `${data.linkCount} artículos` }}
      </span>
    </div>
  </div>
</template>
