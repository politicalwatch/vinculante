<script setup lang="ts">
import { VueFlow, useVueFlow } from '@vue-flow/core'
import type { NodeMouseEvent } from '@vue-flow/core'
import { useElementSize } from '@vueuse/core'
import type { Match, Proposal, Section, TargetDocument } from '~/types/api'
import ArticleNode from '~/components/experimental/ArticleNode.vue'
import ProposalNode from '~/components/experimental/ProposalNode.vue'
import GraphFilterToolbar from '~/components/experimental/GraphFilterToolbar.vue'
import {
  FETCH_MATCH_DEGREES,
  type ArticleNodeData,
  type ProposalNodeData
} from '~/composables/useExperimentalGraph'

const FLOW_ID = 'experimental-graph'

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

useSeoMeta({ title: () => `Exploración — ${target.value?.title ?? ''} — Vinculante` })

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

const flowContainer = ref<HTMLElement | null>(null)
const { width: flowWidth, height: flowHeight } = useElementSize(flowContainer)

const {
  nodes,
  edges,
  filters,
  linkCountBounds,
  totals,
  visible,
  hasActiveFilters,
  hasSelection,
  toggleArticle,
  toggleProposal,
  clearSelection,
  resetFilters
} = useExperimentalGraph(sections, proposals, matches, flowWidth, flowHeight)

const { fitView } = useVueFlow({ id: FLOW_ID })

const nodeTypes = {
  article: markRaw(ArticleNode),
  proposal: markRaw(ProposalNode)
}

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

async function zoomToFocus(focus: boolean) {
  await nextTick()
  await nextTick()

  if (!focus) {
    await fitView({ padding: 0.15, duration: 450, minZoom: 0.05 })
    return
  }

  const focusIds = nodes.value
    .filter((n) => {
      if (n.type === 'article') {
        const data = n.data as ArticleNodeData
        return data.selected || data.highlighted
      }
      if (n.type === 'proposal') {
        const data = n.data as ProposalNodeData
        return data.selected || data.highlighted
      }
      return false
    })
    .map(n => n.id)

  await fitView({
    nodes: focusIds.length > 0 ? focusIds : undefined,
    padding: 0.28,
    duration: 450,
    maxZoom: 1.5
  })
}

async function onNodeClick({ node }: NodeMouseEvent) {
  if (node.type === 'article') {
    const sectionId = (node.data as ArticleNodeData).sectionId
    const selecting = !(node.data as ArticleNodeData).selected
    toggleArticle(sectionId)
    await zoomToFocus(selecting)
    return
  }

  if (node.type === 'proposal') {
    const proposalId = (node.data as ProposalNodeData).proposalId
    const selecting = !(node.data as ProposalNodeData).selected
    toggleProposal(proposalId)
    await zoomToFocus(selecting)
  }
}

async function onPaneClick() {
  if (!hasSelection.value) return
  clearSelection()
  await zoomToFocus(false)
}

async function onClearSelection() {
  clearSelection()
  await zoomToFocus(false)
}
</script>

<template>
  <div class="h-full flex flex-col min-h-0">
    <div class="shrink-0 border-b border-default px-4 md:px-6 py-3 flex items-center justify-between gap-4">
      <div class="min-w-0">
        <p class="text-xs text-muted uppercase tracking-wide">
          Exploración experimental
        </p>
        <h1 class="text-lg font-semibold text-highlighted truncate">
          {{ target?.title }}
        </h1>
      </div>
      <div class="flex items-center gap-3 text-xs text-muted shrink-0">
        <span>{{ articleCountLabel }}</span>
        <span>{{ proposalCountLabel }}</span>
        <span>{{ matchCountLabel }}</span>
        <UButton
          v-if="hasSelection"
          size="xs"
          color="neutral"
          variant="ghost"
          label="Limpiar selección"
          @click="onClearSelection"
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

    <div
      ref="flowContainer"
      class="flex-1 min-h-0 relative"
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
        <VueFlow
          :id="FLOW_ID"
          v-model:nodes="nodes"
          v-model:edges="edges"
          :node-types="nodeTypes"
          :nodes-draggable="true"
          :nodes-connectable="false"
          :elements-selectable="false"
          :min-zoom="0.05"
          :max-zoom="2"
          fit-view-on-init
          class="experimental-flow"
          @node-click="onNodeClick"
          @pane-click="onPaneClick"
        />
      </ClientOnly>
    </div>
  </div>
</template>

<style scoped>
.experimental-flow {
  width: 100%;
  height: 100%;
}

.experimental-flow :deep(.vue-flow__node) {
  transition:
    transform 0.45s cubic-bezier(0.22, 1, 0.36, 1),
    opacity 0.35s ease;
}

.experimental-flow :deep(.vue-flow__edge-path) {
  transition: opacity 0.35s ease, stroke 0.35s ease;
}
</style>
