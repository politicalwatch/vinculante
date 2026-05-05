<script setup lang="ts">
import type { TargetDocument } from '~/types/api'

defineProps<{
  target: TargetDocument | null | undefined
}>()
</script>

<template>
  <div class="flex flex-1 overflow-hidden">
    <div class="w-1/2 border-r border-default">
      <SummaryPanel :summary="target?.summary ?? null" />
    </div>
    <div class="w-1/2 overflow-y-auto">
      <StatsPanel :stats="target?.stats ?? null" />
    </div>
  </div>
</template>
