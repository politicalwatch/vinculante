<script setup lang="ts">
import type { Match, Section, TargetDocument } from '~/types/api'

const route = useRoute()
const id = Number(route.params.id)
const api = useApi()

const [
  { data: target, error: targetError },
  { data: sections, error: sectionsError },
  { data: matchCounts }
] = await Promise.all([
  useFetch<TargetDocument>(`/targets/${id}`, { $fetch: api }),
  useFetch<Section[]>('/sections', { $fetch: api, query: { target_id: id } }),
  useFetch<Record<number, number>>('/matches/counts', {
    $fetch: api,
    query: { target_id: id, degree: ['medio', 'alto'] }
  })
])

if (targetError.value) {
  throw createError({ statusCode: 404, message: 'Documento no encontrado' })
}

useSeoMeta({ title: () => `${target.value?.title ?? ''} — Vinculante` })

const selectedSectionId = ref<number | null>(null)
const hoveredMatchId = ref<number | null>(null)
const selectedMatchId = ref<number | null>(null)
const hideUnmatched = ref(false)
const statsOpen = ref(false)

const filteredSections = computed(() => {
  const all = sections.value ?? []
  if (!hideUnmatched.value) return all
  return all.filter(s => !s.is_matchable || (matchCounts.value?.[s.id] ?? 0) > 0)
})

const degreeRank: Record<string, number> = { alto: 0, medio: 1, bajo: 2, ninguno: 3 }

const { data: matches, status: matchesStatus } = useAsyncData(
  'section-matches',
  () => {
    if (selectedSectionId.value === null) return Promise.resolve([])
    return api<Match[]>('/matches', {
      query: { section_id: selectedSectionId.value, degree: ['medio', 'alto'] }
    })
  },
  { watch: [selectedSectionId] }
)

const sectionsPanel = ref<HTMLElement | null>(null)

function selectSection(sectionId: number) {
  selectedSectionId.value = sectionId
}

function scrollToSelectedSection() {
  const id = selectedSectionId.value
  if (id === null) return
  nextTick(() => {
    sectionsPanel.value
      ?.querySelector<HTMLElement>(`[data-section-id="${id}"]`)
      ?.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
  })
}

watch(selectedSectionId, () => {
  hoveredMatchId.value = null
  selectedMatchId.value = null
  scrollToSelectedSection()
})

watch(selectedMatchId, (id) => {
  if (id !== null) scrollToSelectedSection()
})

const sortedMatches = computed(() => {
  const list = matches.value ?? []
  return [...list].sort((a, b) => {
    const da = degreeRank[a.degree ?? 'ninguno'] ?? 99
    const db = degreeRank[b.degree ?? 'ninguno'] ?? 99
    if (da !== db) return da - db
    return (b.confidence ?? 0) - (a.confidence ?? 0)
  })
})

const activeMatchId = computed(() => hoveredMatchId.value ?? selectedMatchId.value)

const activeSpans = computed<[number, number][]>(() => {
  if (activeMatchId.value === null) return []
  const match = matches.value?.find(m => m.id === activeMatchId.value)
  return match?.section_spans ?? []
})

// Compute depth per section for indentation
const depthMap = computed(() => {
  const map = new Map<number, number>()
  const secs = sections.value ?? []

  function getDepth(id: number): number {
    if (map.has(id)) return map.get(id)!
    const section = secs.find(s => s.id === id)
    if (!section || section.parent_id === null) {
      map.set(id, 0)
      return 0
    }
    const depth = getDepth(section.parent_id) + 1
    map.set(id, depth)
    return depth
  }

  for (const s of secs) getDepth(s.id)
  return map
})
</script>

<template>
  <div class="h-full flex flex-col">
    <!-- Target header -->
    <div class="border-b border-default px-6 py-4 shrink-0">
      <NuxtLink to="/" class="text-sm text-muted hover:text-default flex items-center gap-1 mb-2">
        <UIcon name="i-lucide-chevron-left" class="size-4" />
        Todos los documentos
      </NuxtLink>
      <div class="flex items-start justify-between gap-4">
        <div>
          <h1 class="text-2xl font-semibold text-highlighted">
            {{ target?.title }}
          </h1>
          <p class="text-sm text-muted mt-0.5">
            {{ target?.author }}
            <template v-if="target?.date"> · {{ target.date }}</template>
            <template v-if="target?.version"> · v{{ target.version }}</template>
          </p>
        </div>
        <UModal
          v-if="target?.stats"
          v-model:open="statsOpen"
          title="Estadísticas de vinculación del documento"
          :ui="{ content: 'sm:max-w-5xl' }"
        >
          <UButton
            icon="i-lucide-chart-bar"
            color="neutral"
            variant="ghost"
            size="sm"
            label="Mostrar estadísticas"
          />
          <template #body>
            <StatsPanel :stats="target.stats" />
          </template>
        </UModal>
      </div>
    </div>

    <UAlert
      v-if="sectionsError"
      color="error"
      icon="i-lucide-alert-circle"
      title="Error al cargar las secciones"
      class="m-4"
    />

    <!-- Split view -->
    <div v-else class="flex flex-1 overflow-hidden">
      <!-- Left: sections list -->
      <div ref="sectionsPanel" class="w-7/12 border-r border-default overflow-y-auto">
        <!-- Filter bar -->
        <div class="px-4 py-2 border-b border-default sticky top-0 bg-default z-10 flex items-center justify-between">
          <span class="text-xs text-muted">{{ filteredSections.length }} secciones</span>
          <USwitch
            v-model="hideUnmatched"
            label="Ocultar sin vinculación"
            size="xs"
          />
        </div>

        <div v-if="!sections?.length" class="text-center py-16 text-muted text-sm">
          Este documento no tiene secciones.
        </div>
        <div v-else-if="filteredSections.length === 0" class="text-center py-16 text-muted text-sm">
          Ninguna sección con vinculaciones.
        </div>

        <SectionItem
          v-for="section in filteredSections"
          :key="section.id"
          :data-section-id="section.id"
          :section="section"
          :depth="depthMap.get(section.id) ?? 0"
          :active="selectedSectionId === section.id"
          :spans="selectedSectionId === section.id ? activeSpans : []"
          :match-count="matchCounts?.[section.id] ?? 0"
          @click="selectSection(section.id)"
        />
      </div>

      <!-- Right: matches panel -->
      <div class="w-5/12 overflow-hidden">
        <MatchesPanel
          :section-id="selectedSectionId"
          :matches="sortedMatches"
          :loading="matchesStatus === 'pending'"
          :hovered-match-id="hoveredMatchId"
          :selected-match-id="selectedMatchId"
          @hover-match="hoveredMatchId = $event"
          @leave-match="hoveredMatchId = null"
          @select-match="selectedMatchId = selectedMatchId === $event ? null : $event"
        />
      </div>
    </div>
  </div>
</template>
