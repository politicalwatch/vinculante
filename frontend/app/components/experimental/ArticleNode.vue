<script setup lang="ts">
import { Handle, Position } from '@vue-flow/core'
import type { ArticleNodeData } from '~/composables/useExperimentalGraph'

defineProps<{
  data: ArticleNodeData
}>()
</script>

<template>
  <div
    class="relative w-85 rounded-lg border bg-default p-4 shadow-sm cursor-pointer transition-shadow"
    :class="data.selected
      ? 'border-primary ring-2 ring-primary/30'
      : 'border-default'"
  >
    <p class="text-[10px] font-bold uppercase tracking-wide text-primary">
      {{ data.sectionNumber ? `Artículo ${data.sectionNumber}` : 'Artículo' }}
    </p>
    <p class="mt-2 text-sm text-default leading-relaxed line-clamp-4">
      {{ data.text }}
    </p>
    <Handle
      type="source"
      :position="Position.Right"
      class="size-2! bg-primary/40! border-0!"
    />
  </div>
</template>
