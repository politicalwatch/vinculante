<script setup lang="ts">
import type { TargetDocument } from '~/types/api'

defineProps<{
  target: TargetDocument | null | undefined
}>()

defineEmits<{ 'select-section': [sectionId: number] }>()
</script>

<template>
  <div class="flex flex-col md:flex-row flex-1 overflow-y-auto md:overflow-hidden">
    <div class="w-full md:w-1/2 order-2 md:order-1 border-t md:border-t-0 md:border-r border-default">
      <SummaryPanel :summary="target?.summary ?? null" />
    </div>
    <div class="w-full md:w-1/2 order-1 md:order-2 md:overflow-y-auto">
      <StatsPanel :stats="target?.stats ?? null" @select-section="$emit('select-section', $event)" />
    </div>
  </div>
</template>
