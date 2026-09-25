<script setup lang="ts">
import { useElementSize } from '@vueuse/core'
import type { Match, Proposal, Section } from '~/types/api'
import type { BoardView } from '~/composables/useEditorialBoard'
import GraphFilterToolbar from '~/components/experimental/GraphFilterToolbar.vue'
import ArticleMinimap from '~/components/experimental/editorial/ArticleMinimap.vue'
import EditorialArticleCard from '~/components/experimental/editorial/EditorialArticleCard.vue'
import FloatingProposalCard from '~/components/experimental/editorial/FloatingProposalCard.vue'
import ProposalExplorer from '~/components/experimental/editorial/ProposalExplorer.vue'
import { FETCH_MATCH_DEGREES } from '~/utils/graphFilters'
import { ARTICLE_COLUMN_WIDTH, useEditorialBoard } from '~/composables/useEditorialBoard'

definePageMeta({ layout: 'editorial', colorMode: 'light' })

/** The header drives the board view through the URL, so both stay in sync. */
const VIEW_BY_QUERY: Record<string, BoardView> = {
  vinculaciones: 'articles',
  propuestas: 'proposals'
}

const route = useRoute()
const id = Number(route.params.id)
const api = useApi()

const { data: target, error: targetError } = await useTargetDocument(id)

if (targetError.value) {
  throw createError({ statusCode: 404, message: 'Documento no encontrado' })
}

useSeoMeta({ title: () => `Exploración v3 — ${target.value?.title ?? ''} — Vinculante` })

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

const proposalLayer = ref<HTMLElement | null>(null)
const proposalExplorer = ref<{ clearSelection: () => void } | null>(null)
const { width: layerWidth, height: layerHeight } = useElementSize(proposalLayer)

const {
  filters,
  view,
  proponent,
  proponentOptions,
  linkCountBounds,
  totals,
  visible,
  hasActiveFilters,
  articles,
  proposals: boardProposals,
  filteredProposals,
  filteredMatches,
  stackConnectors,
  surfaceSize,
  stackHeight,
  selectedArticleId,
  hasSelection,
  relatedProposalIds,
  selectArticle,
  clearSelection,
  isExpanded,
  toggleExpanded,
  toggleProposalExpanded,
  setProposalHeight,
  articleOpacity,
  resetFilters
} = useEditorialBoard(sections, proposals, matches, layerWidth, layerHeight)

const loading = computed(
  () =>
    sectionsStatus.value === 'pending'
    || proposalsStatus.value === 'pending'
    || matchesStatus.value === 'pending'
)

const loadError = computed(
  () => sectionsError.value || proposalsError.value || matchesError.value
)

// ---------------------------------------------------------------------------
// Independent scroll areas
// ---------------------------------------------------------------------------

const articleScroll = ref<HTMLElement | null>(null)
const articleList = ref<HTMLElement | null>(null)
const minimapScrollRatio = ref(0)
const cardRefs = new Map<number, HTMLElement>()

function setCardRef(sectionId: number, el: unknown) {
  if (el instanceof HTMLElement) cardRefs.set(sectionId, el)
  else cardRefs.delete(sectionId)
}

/** Keep the minimap in register with the article column without coupling scrollbars. */
function onArticleScroll() {
  const el = articleScroll.value
  if (!el) return
  const scrollable = el.scrollHeight - el.clientHeight
  minimapScrollRatio.value = scrollable > 0 ? el.scrollTop / scrollable : 0
}

/**
 * Selecting scrolls the article to the top of its column so the proposal stack,
 * which always starts at the top of its own scroll area, lines up with it.
 */
function scrollArticleToTop(sectionId: number) {
  const container = articleScroll.value
  const card = cardRefs.get(sectionId)
  if (!container || !card) return
  container.scrollTo({ top: Math.max(0, card.offsetTop - 8), behavior: 'smooth' })
}

function onSelectArticle(sectionId: number) {
  const wasSelected = selectedArticleId.value === sectionId
  selectArticle(sectionId)
  proposalLayer.value?.scrollTo({ top: 0, left: 0, behavior: 'smooth' })
  if (!wasSelected) scrollArticleToTop(sectionId)
}

/** Same as picking the article on the left, then keeps the clicked card in view in the new stack. */
async function onSelectArticleFromProposal(proposalId: number, sectionId: number) {
  onSelectArticle(sectionId)
  await nextTick()
  const card = boardProposals.value.find(p => p.proposalId === proposalId)
  if (!card || card.opacity === 0) return
  proposalLayer.value?.scrollTo({ top: Math.max(0, card.y - 8), left: 0, behavior: 'smooth' })
}

function onMinimapSelect(sectionId: number) {
  onSelectArticle(sectionId)
}

function onBackgroundClick() {
  if (hasSelection.value) clearSelection()
}

watch(
  () => route.query.vista,
  (vista) => {
    view.value = VIEW_BY_QUERY[String(vista)] ?? 'articles'
  },
  { immediate: true }
)

watch(view, (next) => {
  if (next === 'articles') {
    proposalExplorer.value?.clearSelection()
  } else {
    clearSelection()
  }
})

const surfaceStyle = computed(() => {
  if (hasSelection.value) {
    return {
      width: '100%',
      height: `${Math.max(stackHeight.value, layerHeight.value)}px`
    }
  }
  return {
    width: `${surfaceSize.value.width}px`,
    height: `${surfaceSize.value.height}px`
  }
})

const articleBadge = computed(() => `${visible.value.articles} VISIBLES`)

const proposalBadge = computed(() => {
  if (hasSelection.value) {
    const count = relatedProposalIds.value.length
    return count === 1 ? '1 VINCULADA' : `${count} VINCULADAS`
  }
  return `${boardProposals.value.length} VISIBLES`
})

const matchCountLabel = computed(() =>
  hasActiveFilters.value
    ? `${visible.value.matches} / ${totals.value.matches} vinculaciones`
    : `${visible.value.matches} vinculaciones`
)

const emptyStateMessage = computed(() => {
  if (hasSelection.value && relatedProposalIds.value.length === 0) {
    return 'Este artículo no tiene vinculaciones con el grado mínimo seleccionado.'
  }
  if (!hasSelection.value && boardProposals.value.length === 0) {
    return 'Ninguna propuesta cumple los filtros actuales.'
  }
  return null
})
</script>

<template>
  <div class="flex h-full min-h-0 flex-col">
    <GraphFilterToolbar
      v-model:proponent="proponent"
      :filters="filters"
      :link-count-bounds="linkCountBounds"
      :has-active-filters="hasActiveFilters"
      :show-article-link-range="view === 'articles'"
      :show-proposal-article-range="view === 'proposals'"
      :proponent-options="proponentOptions"
      @update:filters="Object.assign(filters, $event)"
      @reset="resetFilters"
    />

    <div
      v-if="loading"
      class="flex-1 flex items-center justify-center"
    >
      <UIcon
        name="i-lucide-loader-circle"
        class="size-8 animate-spin text-ed-muted"
      />
    </div>

    <UAlert
      v-else-if="loadError"
      color="error"
      icon="i-lucide-alert-circle"
      title="Error al cargar los datos"
      class="m-6"
    />

    <div
      v-else-if="view === 'proposals'"
      class="flex-1 min-h-0 flex"
    >
      <ProposalExplorer
        ref="proposalExplorer"
        :proposals="filteredProposals"
        :matches="filteredMatches"
        :articles="articles"
      />
    </div>

    <div
      v-else
      class="flex-1 min-h-0 flex"
    >
      <ArticleMinimap
        :articles="articles"
        :selected-article-id="selectedArticleId"
        :scroll-ratio="minimapScrollRatio"
        @select="onMinimapSelect"
      />

      <section
        class="flex min-h-0 shrink-0 flex-col border-r border-ed-border"
        :style="{ width: `${ARTICLE_COLUMN_WIDTH + 48}px` }"
      >
        <div class="flex shrink-0 items-center gap-3 px-6 pt-5 pb-3">
          <h2 class="text-xs font-semibold tracking-widest text-ed-muted uppercase">
            Artículos de Ley
          </h2>
          <span class="inline-flex h-5 items-center rounded bg-ed-ink/8 px-2 text-2xs font-semibold tracking-wide whitespace-nowrap text-ed-ink">
            {{ articleBadge }}
          </span>
        </div>

        <div
          ref="articleScroll"
          class="flex-1 min-h-0 overflow-y-auto overscroll-contain px-6 pb-8"
          @scroll="onArticleScroll"
        >
          <div
            ref="articleList"
            class="relative flex flex-col gap-3"
          >
            <EditorialArticleCard
              v-for="article in articles"
              :key="article.sectionId"
              :ref="el => setCardRef(article.sectionId, (el as { $el?: unknown })?.$el ?? el)"
              :article="article"
              :selected="article.sectionId === selectedArticleId"
              :expanded="isExpanded(article.sectionId)"
              :opacity="articleOpacity(article.sectionId)"
              @select="onSelectArticle(article.sectionId)"
              @toggle-expanded="toggleExpanded(article.sectionId)"
            />

            <p
              v-if="articles.length === 0"
              class="py-8 text-center text-sm text-ed-muted"
            >
              Ningún artículo cumple los filtros actuales.
            </p>
          </div>
        </div>
      </section>

      <section class="flex-1 min-w-0 flex flex-col min-h-0">
        <div class="flex shrink-0 items-center gap-3 px-6 pt-5 pb-3">
          <h2 class="text-xs font-semibold tracking-widest text-ed-muted uppercase">
            Propuestas Ciudadanas
          </h2>
          <span class="inline-flex h-5 items-center rounded bg-ed-ink/8 px-2 text-2xs font-semibold tracking-wide whitespace-nowrap text-ed-ink">
            {{ proposalBadge }}
          </span>
          <span class="ml-auto text-11 text-ed-muted tabular-nums">
            {{ matchCountLabel }}
          </span>
          <UButton
            v-if="hasSelection"
            size="xs"
            color="neutral"
            variant="ghost"
            label="Limpiar selección"
            @click="clearSelection"
          />
        </div>

        <div
          ref="proposalLayer"
          class="relative min-h-0 flex-1 overscroll-contain"
          :class="hasSelection ? 'overflow-x-hidden overflow-y-auto' : 'overflow-auto'"
          @click.self="onBackgroundClick"
        >
          <div
            class="relative"
            :style="surfaceStyle"
            @click.self="onBackgroundClick"
          >
            <svg
              v-if="stackConnectors"
              class="pointer-events-none absolute top-0 left-0 overflow-visible text-ed-accent"
              :width="stackConnectors.width"
              :height="stackConnectors.height"
              aria-hidden="true"
            >
              <path
                :d="stackConnectors.spine"
                fill="none"
                stroke="currentColor"
                stroke-width="1"
                opacity="0.4"
              />
              <path
                v-for="tick in stackConnectors.ticks"
                :key="tick.proposalId"
                :d="tick.path"
                fill="none"
                stroke="currentColor"
                stroke-width="1"
                opacity="0.55"
              />
            </svg>

            <FloatingProposalCard
              v-for="proposal in boardProposals"
              :key="proposal.proposalId"
              :proposal="proposal"
              wide-when-expanded
              :selected-article-id="selectedArticleId"
              @toggle="toggleProposalExpanded(proposal.proposalId)"
              @measure="setProposalHeight(proposal.proposalId, $event)"
              @select-article="onSelectArticleFromProposal(proposal.proposalId, $event)"
            />
          </div>

          <p
            v-if="emptyStateMessage"
            class="absolute inset-x-0 top-24 px-8 text-center text-sm text-ed-muted"
          >
            {{ emptyStateMessage }}
          </p>
        </div>
      </section>
    </div>
  </div>
</template>
