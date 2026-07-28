<script setup lang="ts">
import { Handle, Position } from '@vue-flow/core'
import type { ProposalNodeData } from '~/composables/useExperimentalGraph'

defineProps<{
  data: ProposalNodeData
}>()
</script>

<template>
  <div
    class="relative w-85 rounded-lg border bg-default overflow-hidden shadow-sm flex transition-shadow"
    :class="data.highlighted
      ? 'border-warning ring-2 ring-warning/25'
      : 'border-default'"
  >
    <Handle
      type="target"
      :position="Position.Left"
      class="size-2! bg-warning/40! border-0!"
    />
    <div class="w-1 shrink-0 bg-warning" />
    <div class="p-4 min-w-0 flex-1">
      <p class="text-[10px] font-bold uppercase tracking-wide text-warning">
        Propuesta #{{ data.proposalId }}
      </p>
      <p class="mt-2 text-sm text-default leading-relaxed line-clamp-4">
        {{ data.text }}
      </p>
    </div>
  </div>
</template>
