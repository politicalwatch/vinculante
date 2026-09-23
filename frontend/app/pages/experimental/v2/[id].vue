<script setup lang="ts">
import { useElementSize } from '@vueuse/core'
import type { Match, Proposal, Section, TargetDocument } from '~/types/api'
import GraphFilterToolbar from '~/components/experimental/GraphFilterToolbar.vue'
import BallGraphCanvas from '~/components/experimental/BallGraphCanvas.vue'
import {
  FETCH_MATCH_DEGREES,
  useExperimentalBallGraph,
  type BallSimNode
} from '~/composables/useExperimentalBallGraph'

const route = useRoute()
const id = Number(route.params.id)
const api = useApi()

const { data: target, error: targetError } = await useFetch<TargetDocument>(
  `/targets/${id}`,
  { $fetch: api }
)

if (targetError.value) {
  throw createError({ statusCode: 404, message: 'Documento no encontrado' })
}

useSeoMeta({ title: () => `Exploración v2 — ${target.value?.title ?? ''} — Vinculante` })

const { data: sections, status: sectionsStatus, error: sectionsError } = useFetch<Section[]>(
  '/sections',
  { $fetch: api, query: { target_id: id } }
)

const { data: proposals, status: proposalsStatus, error: proposalsError } = useFetch<Proposal[]>(
  '/proposals',
  { $fetch: api, query: { target_id: id } }
)

const { data: matches, status: matchesStatus, error: matchesError } = useFetch<Match[]>(
  '/matches',
  { $fetch: api, query: { target_id: id, degree: FETCH_MATCH_DEGREES } }
)

const canvasContainer = ref<HTMLElement | null>(null)
const { width: canvasWidth, height: canvasHeight } = useElementSize(canvasContainer)

const {
  simNodes,
  simLinks,
  layoutMode,
  filters,
  linkCountBounds,
  totals,
  visible,
  hasActiveFilters,
  hasSelection,
  selectedDetail,
  dimmedOpacity,
  toggleArticle,
  toggleProposal,
  clearSelection,
  resetFilters,
  startDrag,
  dragNode,
  endDrag
} = useExperimentalBallGraph(sections, proposals, matches, canvasWidth, canvasHeight)

const layoutOptions: Array<{ label: string, value: 'force' | 'circles' }> = [
  { label: 'Fuerza', value: 'force' },
  { label: 'Círculos', value: 'circles' }
]

const loading = computed(
  () =>
    sectionsStatus.value === 'pending'
    || proposalsStatus.value === 'pending'
    || matchesStatus.value === 'pending'
)

const loadError = computed(
  () => sectionsError.value || proposalsError.value || matchesError.value
)

const articleCountLabel = computed(() => {
  if (!hasActiveFilters.value) return `${totals.value.articles} artículos`
  return `${visible.value.articles} / ${totals.value.articles} artículos`
})

const proposalCountLabel = computed(() => {
  if (!hasActiveFilters.value) return `${totals.value.proposals} propuestas`
  return `${visible.value.proposals} / ${totals.value.proposals} propuestas`
})

const matchCountLabel = computed(() => {
  if (!hasActiveFilters.value) return `${visible.value.matches} vinculaciones`
  return `${visible.value.matches} / ${totals.value.matches} vinculaciones`
})

function onNodeClick(node: BallSimNode) {
  if (node.kind === 'article') {
    toggleArticle(node.entityId)
    return
  }
  toggleProposal(node.entityId)
}

function onPaneClick() {
  if (!hasSelection.value) return
  clearSelection()
}
</script>

<template>
  <div class="h-full flex flex-col min-h-0">
    <div class="shrink-0 border-b border-default px-4 md:px-6 py-3 flex items-center justify-between gap-4">
      <div class="min-w-0">
        <p class="text-xs text-muted uppercase tracking-wide">
          Exploración experimental v2
        </p>
        <h1 class="text-lg font-semibold text-highlighted truncate">
          {{ target?.title }}
        </h1>
      </div>
      <div class="flex items-center gap-3 text-xs text-muted shrink-0">
        <UTabs
          v-model="layoutMode"
          :items="layoutOptions"
          :content="false"
          color="neutral"
          variant="pill"
          size="xs"
          class="w-auto"
        />
        <span>{{ articleCountLabel }}</span>
        <span>{{ proposalCountLabel }}</span>
        <span>{{ matchCountLabel }}</span>
        <UButton
          v-if="hasSelection"
          size="xs"
          color="neutral"
          variant="ghost"
          label="Limpiar selección"
          @click="clearSelection"
        />
      </div>
    </div>

    <GraphFilterToolbar
      :filters="filters"
      :link-count-bounds="linkCountBounds"
      :has-active-filters="hasActiveFilters"
      @update:filters="Object.assign(filters, $event)"
      @reset="resetFilters"
    />

    <div class="flex-1 min-h-0 flex relative">
      <div
        ref="canvasContainer"
        class="flex-1 min-w-0 min-h-0 relative"
      >
        <div
          v-if="loading"
          class="absolute inset-0 flex items-center justify-center"
        >
          <UIcon
            name="i-lucide-loader-circle"
            class="size-8 animate-spin text-muted"
          />
        </div>

        <UAlert
          v-else-if="loadError"
          color="error"
          icon="i-lucide-alert-circle"
          title="Error al cargar los datos"
          class="m-4"
        />

        <ClientOnly v-else>
          <BallGraphCanvas
            :nodes="simNodes"
            :links="simLinks"
            :dimmed-opacity="dimmedOpacity"
            :draggable="layoutMode === 'force'"
            @node-click="onNodeClick"
            @pane-click="onPaneClick"
            @drag-start="startDrag"
            @drag="(id, x, y) => dragNode(id, x, y)"
            @drag-end="endDrag"
          />
        </ClientOnly>
      </div>

      <aside
        v-if="selectedDetail"
        class="w-full max-w-sm shrink-0 border-l border-default bg-default overflow-y-auto"
      >
        <div class="p-4 flex flex-col gap-3">
          <div class="flex items-start justify-between gap-2">
            <div class="min-w-0">
              <p class="text-xs text-muted uppercase tracking-wide">
                {{ selectedDetail.kind === 'article' ? 'Artículo' : 'Propuesta' }}
              </p>
              <h2 class="text-base font-semibold text-highlighted">
                {{ selectedDetail.title }}
              </h2>
              <p class="text-xs text-muted mt-1">
                {{ selectedDetail.linkCount }}
                {{ selectedDetail.kind === 'article' ? 'vinculaciones' : 'artículos' }}
              </p>
            </div>
            <UButton
              icon="i-lucide-x"
              color="neutral"
              variant="ghost"
              size="xs"
              aria-label="Cerrar"
              @click="clearSelection"
            />
          </div>
          <p class="text-sm text-default whitespace-pre-wrap leading-relaxed">
            {{ selectedDetail.text }}
          </p>
        </div>
      </aside>
    </div>
  </div>
</template>
