<script setup lang="ts">
import { useElementSize } from '@vueuse/core'
import type { Match, Proposal } from '~/types/api'
import EditorialArticleCard from '~/components/experimental/editorial/EditorialArticleCard.vue'
import FloatingProposalCard from '~/components/experimental/editorial/FloatingProposalCard.vue'
import {
  PROPOSAL_CARD_WIDTH,
  type EditorialArticle
} from '~/composables/useEditorialBoard'
import { COLUMN_GAP, useProposalExplorer } from '~/composables/useProposalExplorer'

const props = defineProps<{
  proposals: Proposal[]
  matches: Match[]
  articles: EditorialArticle[]
}>()

const emit = defineEmits<{
  clearSelection: []
}>()

const proposalLayer = ref<HTMLElement | null>(null)
const { width: layerWidth, height: layerHeight } = useElementSize(proposalLayer)

const {
  grouping,
  hasSelection,
  selectedProposal,
  linkedArticles,
  boardProposals,
  columns,
  surfaceSize,
  visibleCount,
  selectProposal,
  clearSelection,
  toggleProposalExpanded,
  setProposalHeight,
  isArticleExpanded,
  toggleArticleExpanded
} = useProposalExplorer(
  () => props.proposals,
  () => props.matches,
  () => props.articles,
  layerWidth,
  layerHeight
)

const groupingOptions: Array<{ label: string, value: 'none' | 'linkCount' }> = [
  { label: 'Sin agrupar', value: 'none' },
  { label: 'Nº de artículos', value: 'linkCount' }
]

const surfaceStyle = computed(() => ({
  width: `${surfaceSize.value.width}px`,
  height: `${surfaceSize.value.height}px`
}))

const emptyStateMessage = computed(() => {
  if (hasSelection.value) return null
  if (boardProposals.value.length === 0) {
    return 'Ninguna propuesta cumple los filtros actuales.'
  }
  return null
})

function onCardClick(proposalId: number) {
  selectProposal(proposalId)
}

function onClearSelection() {
  clearSelection()
  emit('clearSelection')
}

watch(hasSelection, (focused) => {
  if (!focused) return
  proposalLayer.value?.scrollTo({ top: 0, left: 0, behavior: 'smooth' })
})

defineExpose({ clearSelection })
</script>

<template>
  <section class="proposal-explorer flex-1 min-w-0 flex flex-col min-h-0">
    <div class="column-header">
      <h2>Propuestas</h2>
      <span class="column-badge">{{ visibleCount }} VISIBLES</span>

      <div class="ml-auto flex items-center gap-4 flex-wrap justify-end">
        <div class="flex items-center gap-2">
          <span class="text-[11px] text-(--ed-muted) whitespace-nowrap">Agrupar por</span>
          <div class="grouping-toggle">
            <button
              v-for="option in groupingOptions"
              :key="option.value"
              type="button"
              class="grouping-chip"
              :class="grouping === option.value ? 'is-active' : ''"
              :aria-pressed="grouping === option.value"
              @click="grouping = option.value"
            >
              {{ option.label }}
            </button>
          </div>
        </div>

        <UButton
          v-if="hasSelection"
          size="xs"
          color="neutral"
          variant="ghost"
          label="Volver"
          icon="i-lucide-arrow-left"
          @click="onClearSelection"
        />
      </div>
    </div>

    <div
      ref="proposalLayer"
      class="proposal-layer"
      :class="hasSelection ? 'is-focused' : 'is-idle'"
    >
      <Transition
        name="explorer-fade"
        mode="out-in"
      >
        <div
          v-if="hasSelection && selectedProposal"
          key="focus"
          class="focus-panel"
        >
          <div class="focus-proposal">
            <FloatingProposalCard
              :proposal="{
                ...selectedProposal,
                x: 0,
                y: 0,
                floating: false,
                stacked: true,
                expanded: true,
                opacity: 1,
                zIndex: 1
              }"
              @toggle="toggleProposalExpanded(selectedProposal.proposalId)"
              @measure="setProposalHeight(selectedProposal.proposalId, $event)"
            />
          </div>

          <div class="focus-articles">
            <div class="focus-articles-header">
              <h3>Artículos vinculados</h3>
              <span class="column-badge">
                {{ linkedArticles.length === 1
                  ? '1 VINCULADO'
                  : `${linkedArticles.length} VINCULADOS` }}
              </span>
            </div>

            <div class="focus-articles-list">
              <EditorialArticleCard
                v-for="article in linkedArticles"
                :key="article.sectionId"
                :article="article"
                :selected="false"
                :expanded="isArticleExpanded(article.sectionId)"
                :opacity="1"
                @select="toggleArticleExpanded(article.sectionId)"
                @toggle-expanded="toggleArticleExpanded(article.sectionId)"
              />

              <p
                v-if="linkedArticles.length === 0"
                class="text-sm text-(--ed-muted) py-8 text-center"
              >
                Esta propuesta no tiene artículos vinculados con el grado mínimo seleccionado.
              </p>
            </div>
          </div>
        </div>

        <div
          v-else
          key="browse"
          class="proposal-surface"
          :style="surfaceStyle"
        >
          <template v-if="grouping === 'linkCount'">
            <div
              v-for="(column, index) in columns"
              :key="`band-${column.key}`"
              class="column-band rounded-md border-2 border-(--ed-border)"
              :class="index % 2 === 0 ? 'is-shaded' : 'is-shaded-alternate'"
              :style="{
                left: `${column.x - COLUMN_GAP / 2 + 8}px `,
                width: `${PROPOSAL_CARD_WIDTH + COLUMN_GAP - 12}px`
              }"
            />
            <div
              v-for="column in columns"
              :key="column.key"
              class="column-label"
              :style="{
                left: `${column.x}px`,
                width: `${PROPOSAL_CARD_WIDTH}px`
              }"
            >
              {{ column.label }}
              <span class="column-count">{{ column.proposals.length }}</span>
            </div>
          </template>

          <FloatingProposalCard
            v-for="proposal in boardProposals"
            :key="proposal.proposalId"
            :proposal="proposal"
            @toggle="onCardClick(proposal.proposalId)"
            @measure="setProposalHeight(proposal.proposalId, $event)"
          />

          <p
            v-if="emptyStateMessage"
            class="absolute inset-x-0 top-24 text-center text-sm text-(--ed-muted) px-8"
          >
            {{ emptyStateMessage }}
          </p>
        </div>
      </Transition>
    </div>
  </section>
</template>

<style scoped>
.column-header {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
  padding: 20px 24px 12px;
}

.column-header h2 {
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--ed-muted);
}

.column-badge {
  display: inline-flex;
  align-items: center;
  height: 20px;
  padding: 0 8px;
  border-radius: 4px;
  background: color-mix(in oklab, var(--ed-ink) 8%, transparent);
  color: var(--ed-ink);
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.06em;
  white-space: nowrap;
}

.grouping-toggle {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  padding: 2px;
  border-radius: 8px;
  border: 1px solid var(--ed-border);
  background: var(--ed-surface-sunken, #f5f2ed);
}

.grouping-chip {
  height: 26px;
  padding: 0 10px;
  border-radius: 6px;
  border: none;
  background: transparent;
  color: var(--ed-muted);
  font-size: 11px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.15s ease, color 0.15s ease;
}

.grouping-chip.is-active {
  background: var(--ed-surface);
  color: var(--ed-ink);
  box-shadow: 0 1px 2px rgb(27 58 92 / 0.08);
}

.proposal-layer {
  position: relative;
  flex: 1;
  min-height: 0;
  overscroll-behavior: contain;
}

.proposal-layer.is-idle {
  overflow: auto;
}

.proposal-layer.is-focused {
  overflow: auto;
}

.proposal-surface {
  position: relative;
}

.column-band {
  position: absolute;
  top: 0;
  bottom: 0;
  pointer-events: none;
}

.column-band.is-shaded {
  background: color-mix(in oklab, var(--ed-ink) 3.5%, transparent);
}

.column-band.is-shaded-alternate {
  background: color-mix(in oklab, var(--ed-muted) 4.5%, transparent);
}

.column-label {
  position: absolute;
  top: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--ed-muted);
}

.column-count {
  display: inline-flex;
  align-items: center;
  height: 18px;
  padding: 0 6px;
  border-radius: 4px;
  background: color-mix(in oklab, var(--ed-ink) 8%, transparent);
  color: var(--ed-ink);
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.04em;
}

.focus-panel {
  display: flex;
  gap: 32px;
  padding: 16px 24px 32px;
  min-height: 100%;
}

.focus-proposal {
  position: relative;
  flex-shrink: 0;
  width: v-bind('`${PROPOSAL_CARD_WIDTH}px`');
  min-height: 200px;
}

.focus-proposal :deep(.proposal-position) {
  position: relative;
  width: 100%;
}

.focus-articles {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.focus-articles-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.focus-articles-header h3 {
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--ed-muted);
}

.focus-articles-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-width: 580px;
}

.explorer-fade-enter-active,
.explorer-fade-leave-active {
  transition: opacity 0.25s ease;
}

.explorer-fade-enter-from,
.explorer-fade-leave-to {
  opacity: 0;
}
</style>
