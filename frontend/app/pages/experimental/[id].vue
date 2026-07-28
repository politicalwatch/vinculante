<script setup lang="ts">
import { VueFlow } from '@vue-flow/core'
import type { NodeMouseEvent } from '@vue-flow/core'
import { useElementSize } from '@vueuse/core'
import type { Match, Proposal, Section, TargetDocument } from '~/types/api'
import ArticleNode from '~/components/experimental/ArticleNode.vue'
import ProposalNode from '~/components/experimental/ProposalNode.vue'
import { DEFAULT_MATCH_DEGREES } from '~/composables/useExperimentalGraph'

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
  { $fetch: api, query: { target_id: id, degree: DEFAULT_MATCH_DEGREES } }
)

const flowContainer = ref<HTMLElement | null>(null)
const { width: flowWidth } = useElementSize(flowContainer)

const {
  nodes,
  edges,
  selectedArticleId,
  toggleArticle,
  clearSelection
} = useExperimentalGraph(sections, proposals, matches, flowWidth)

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

const articleCount = computed(
  () => (sections.value ?? []).filter(s => s.is_matchable).length
)

const proposalCount = computed(() => proposals.value?.length ?? 0)

const matchCount = computed(() => matches.value?.length ?? 0)

function onNodeClick({ node }: NodeMouseEvent) {
  if (node.type !== 'article') return
  const sectionId = (node.data as { sectionId: number }).sectionId
  toggleArticle(sectionId)
}

function onPaneClick() {
  if (selectedArticleId.value !== null) clearSelection()
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
        <span>{{ articleCount }} artículos</span>
        <span>{{ proposalCount }} propuestas</span>
        <span>{{ matchCount }} vinculaciones</span>
        <UButton
          v-if="selectedArticleId !== null"
          size="xs"
          color="neutral"
          variant="ghost"
          label="Limpiar selección"
          @click="clearSelection"
        />
      </div>
    </div>

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
          v-model:nodes="nodes"
          v-model:edges="edges"
          :node-types="nodeTypes"
          :nodes-draggable="true"
          :nodes-connectable="false"
          :elements-selectable="false"
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
