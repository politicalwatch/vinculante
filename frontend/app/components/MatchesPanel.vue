<script setup lang="ts">
import type { Match } from '~/types/api'

const props = defineProps<{
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

const authorTypeOptions = [
  { label: 'Todos', value: 'all' },
  { label: 'Ciudadanía', value: 'citizen' },
  { label: 'Grupo de expertos', value: 'academia' }
]
const authorTypeFilter = ref('all')

const degreeOptions = [
  { label: 'Todos', value: 'all' },
  { label: 'Fuerte', value: 'alto' },
  { label: 'Moderado', value: 'medio' }
]
const degreeFilter = ref('all')

const matchesList = ref<HTMLElement | null>(null)
let savedMatchesScroll = 0

onDeactivated(() => { savedMatchesScroll = matchesList.value?.scrollTop ?? 0 })
onActivated(() => { nextTick(() => { if (matchesList.value) matchesList.value.scrollTop = savedMatchesScroll }) })

const filteredMatches = computed(() => {
  return props.matches.filter((m) => {
    if (authorTypeFilter.value !== 'all' && m.proposal.author_type !== authorTypeFilter.value) return false
    if (degreeFilter.value !== 'all' && m.degree !== degreeFilter.value) return false
    return true
  })
})

const hasActiveFilters = computed(
  () => authorTypeFilter.value !== 'all' || degreeFilter.value !== 'all'
)

const subtitle = computed(() => {
  const at = authorTypeFilter.value
  const dg = degreeFilter.value
  if (!hasActiveFilters.value) return 'Todas las propuestas'
  const parts = ['Propuestas']
  if (at !== 'all') parts.push(`de ${authorTypeOptions.find(o => o.value === at)?.label}`)
  if (dg !== 'all') parts.push(`con grado ${degreeOptions.find(o => o.value === dg)?.label}`)
  return parts.join(' ')
})

function clearFilters() {
  authorTypeFilter.value = 'all'
  degreeFilter.value = 'all'
}
</script>

<template>
  <div class="h-full flex flex-col">
    <!-- Empty state: no section selected -->
    <div v-if="sectionId === null" class="flex flex-col items-center justify-center h-full gap-3 px-8 text-center">
      <UIcon name="i-lucide-mouse-pointer-click" class="size-10 text-muted" />
      <p class="text-muted text-sm">
        Selecciona una sección para ver sus vinculaciones con las propuestas ciudadanas.
      </p>
    </div>

    <template v-else>
      <div class="px-4 py-3 border-b border-default shrink-0">
        <h2 class="text-sm font-semibold text-highlighted">
          Vinculaciones
        </h2>
        <p class="text-xs text-muted mt-0.5">
          {{ subtitle }}
          <template v-if="hasActiveFilters">
            ·
            <button
              type="button"
              class="text-primary cursor-pointer hover:underline"
              @click="clearFilters"
            >
              Eliminar filtros
            </button>
          </template>
        </p>
      </div>

      <!-- Filter bar -->
      <div class="px-4 py-2 border-b border-default shrink-0 flex items-center gap-3 flex-wrap">
        <div class="flex items-center gap-2">
          <span class="text-xs text-muted">Tipo de autor</span>
          <USelect
            v-model="authorTypeFilter"
            :items="authorTypeOptions"
            size="xs"
            class="w-32"
          />
        </div>
        <div class="flex items-center gap-2">
          <span class="text-xs text-muted">Grado</span>
          <USelect
            v-model="degreeFilter"
            :items="degreeOptions"
            size="xs"
            class="w-28"
          />
        </div>
        <span class="text-xs text-muted ml-auto">
          Mostrando {{ filteredMatches.length }} de {{ matches.length }} vinculaciones
        </span>
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
          Sin vinculaciones de grado medio o alto para esta sección.
        </p>
      </div>

      <!-- No matches after filter -->
      <div
        v-else-if="filteredMatches.length === 0"
        class="flex flex-col items-center justify-center flex-1 gap-2 px-8 text-center py-12"
      >
        <UIcon name="i-lucide-filter-x" class="size-8 text-muted" />
        <p class="text-sm text-muted">
          Sin vinculaciones para este filtro.
        </p>
      </div>

      <!-- Matches list -->
      <div v-else ref="matchesList" class="overflow-y-auto flex-1 p-4 flex flex-col gap-3">
        <MatchCard
          v-for="match in filteredMatches"
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
