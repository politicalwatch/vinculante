<script setup lang="ts">
import type { Match } from '~/types/api'

defineProps<{
  sectionId: number | null
  matches: Match[]
  loading: boolean
  hoveredMatchId: number | null
  selectedMatchId: number | null
}>()

defineEmits<{
  'hover-match': [id: number]
  'leave-match': [id: number]
  'select-match': [id: number]
}>()
</script>

<template>
  <div class="h-full flex flex-col">
    <!-- Empty state: no section selected -->
    <div v-if="sectionId === null" class="flex flex-col items-center justify-center h-full gap-3 px-8 text-center">
      <UIcon name="i-lucide-mouse-pointer-click" class="size-10 text-muted" />
      <p class="text-muted text-sm">
        Selecciona una sección para ver sus coincidencias con las propuestas ciudadanas.
      </p>
    </div>

    <template v-else>
      <div class="px-4 py-3 border-b border-default shrink-0">
        <h2 class="text-sm font-semibold text-highlighted">
          Coincidencias
        </h2>
        <p class="text-xs text-muted mt-0.5">
          Propuestas con grado medio o alto
        </p>
      </div>

      <!-- Loading state -->
      <div v-if="loading" class="p-4 flex flex-col gap-3">
        <USkeleton v-for="n in 3" :key="n" class="h-28 rounded-lg" />
      </div>

      <!-- No matches found -->
      <div
        v-else-if="matches.length === 0"
        class="flex flex-col items-center justify-center flex-1 gap-2 px-8 text-center py-12"
      >
        <UIcon name="i-lucide-search-x" class="size-8 text-muted" />
        <p class="text-sm text-muted">
          Sin coincidencias medio o alto para esta sección.
        </p>
      </div>

      <!-- Matches list -->
      <div v-else class="overflow-y-auto flex-1 p-4 flex flex-col gap-3">
        <MatchCard
          v-for="match in matches"
          :key="match.id"
          :match="match"
          :selected="match.id === selectedMatchId"
          :hovered="match.id === hoveredMatchId"
          @hover="$emit('hover-match', match.id)"
          @leave="$emit('leave-match', match.id)"
          @click="$emit('select-match', match.id)"
        />
      </div>
    </template>
  </div>
</template>
