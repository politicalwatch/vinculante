<script setup lang="ts">
import type { Match, Section, TargetDocument } from '~/types/api'

const route = useRoute()
const id = Number(route.params.id)
const api = useApi()

const [{ data: target, error: targetError }, { data: sections, error: sectionsError }] = await Promise.all([
  useFetch<TargetDocument>(`/targets/${id}`, { $fetch: api }),
  useFetch<Section[]>('/sections', { $fetch: api, query: { target_id: id } })
])

if (targetError.value) {
  throw createError({ statusCode: 404, message: 'Documento no encontrado' })
}

useSeoMeta({ title: () => `${target.value?.title ?? ''} — Vinculante` })

const selectedSectionId = ref<number | null>(null)

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

function selectSection(sectionId: number) {
  selectedSectionId.value = sectionId
}

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
  <div class="h-[calc(100vh-4rem)] flex flex-col">
    <!-- Target header -->
    <div class="border-b border-default px-6 py-4 shrink-0">
      <NuxtLink to="/" class="text-sm text-muted hover:text-default flex items-center gap-1 mb-2">
        <UIcon name="i-lucide-chevron-left" class="size-4" />
        Todos los documentos
      </NuxtLink>
      <h1 class="text-xl font-semibold text-highlighted">
        {{ target?.title }}
      </h1>
      <p class="text-sm text-muted mt-0.5">
        {{ target?.author }}
        <template v-if="target?.date"> · {{ target.date }}</template>
        <template v-if="target?.version"> · v{{ target.version }}</template>
      </p>
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
      <div class="w-7/12 border-r border-default overflow-y-auto">
        <div v-if="!sections?.length" class="text-center py-16 text-muted text-sm">
          Este documento no tiene secciones.
        </div>

        <SectionItem
          v-for="section in sections"
          :key="section.id"
          :section="section"
          :depth="depthMap.get(section.id) ?? 0"
          :active="selectedSectionId === section.id"
          @click="selectSection(section.id)"
        />
      </div>

      <!-- Right: matches panel -->
      <div class="w-5/12 overflow-hidden">
        <MatchesPanel
          :section-id="selectedSectionId"
          :matches="matches ?? []"
          :loading="matchesStatus === 'pending'"
        />
      </div>
    </div>
  </div>
</template>
