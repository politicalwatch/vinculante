<script setup lang="ts">
import type { TargetDocument } from '~/types/api'

defineProps<{ target: TargetDocument }>()
</script>

<template>
  <UCard
    :ui="{ root: 'hover:ring-primary transition-shadow cursor-pointer' }"
    as="div"
    @click="navigateTo(`/targets/${target.id}`)"
  >
    <div class="flex flex-col gap-3">
      <div>
        <p class="font-semibold text-highlighted line-clamp-2">
          {{ target.title }}
        </p>
        <p class="text-sm text-muted mt-1">
          {{ target.author }}
          <template v-if="target.date"> · {{ target.date }}</template>
          <template v-if="target.version"> · v{{ target.version }}</template>
        </p>
      </div>

      <div class="flex gap-3 pt-1">
        <div class="flex items-center gap-1.5 text-sm text-muted">
          <UIcon name="i-lucide-file-text" class="size-4 shrink-0" />
          <span><strong class="text-default">{{ target.proposal_count }}</strong> propuestas</span>
        </div>
        <div class="flex items-center gap-1.5 text-sm text-muted">
          <UIcon name="i-lucide-link" class="size-4 shrink-0" />
          <span><strong class="text-default">{{ target.match_count }}</strong> vinculaciones</span>
        </div>
      </div>
    </div>
  </UCard>
</template>
