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
  <section class="flex min-h-0 min-w-0 flex-1 flex-col">
    <div class="flex shrink-0 items-center gap-3 px-6 pt-5 pb-3">
      <h2 class="text-xs font-semibold tracking-widest text-ed-muted uppercase">
        Propuestas
      </h2>
      <span class="inline-flex h-5 items-center rounded bg-ed-ink/8 px-2 text-2xs font-semibold tracking-wide whitespace-nowrap text-ed-ink">
        {{ visibleCount }} VISIBLES
      </span>

      <div class="ml-auto flex flex-wrap items-center justify-end gap-4">
        <div class="flex items-center gap-2">
          <span class="text-11 whitespace-nowrap text-ed-muted">Agrupar por</span>
          <div class="inline-flex items-center gap-0.5 rounded-lg border border-ed-border bg-ed-surface-sunken p-0.5">
            <button
              v-for="option in groupingOptions"
              :key="option.value"
              type="button"
              class="h-6 cursor-pointer rounded-md px-2.5 text-11 font-medium transition-colors"
              :class="grouping === option.value ? 'bg-ed-surface text-ed-ink shadow-sm' : 'text-ed-muted'"
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
      class="relative min-h-0 flex-1 overflow-auto overscroll-contain"
    >
      <Transition
        mode="out-in"
        enter-active-class="transition-opacity duration-300"
        enter-from-class="opacity-0"
        leave-active-class="transition-opacity duration-300"
        leave-to-class="opacity-0"
      >
        <div
          v-if="hasSelection && selectedProposal"
          key="focus"
          class="flex min-h-full gap-8 px-6 pt-4 pb-8"
        >
          <div
            class="relative min-h-48 shrink-0"
            :style="{ width: `${PROPOSAL_CARD_WIDTH}px` }"
          >
            <FloatingProposalCard
              in-flow
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

          <div class="flex min-w-0 flex-1 flex-col gap-3">
            <div class="flex items-center gap-3">
              <h3 class="text-xs font-semibold tracking-widest text-ed-muted uppercase">
                Artículos vinculados
              </h3>
              <span class="inline-flex h-5 items-center rounded bg-ed-ink/8 px-2 text-2xs font-semibold tracking-wide whitespace-nowrap text-ed-ink">
                {{ linkedArticles.length === 1
                  ? '1 VINCULADO'
                  : `${linkedArticles.length} VINCULADOS` }}
              </span>
            </div>

            <div class="flex max-w-xl flex-col gap-3">
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
                class="py-8 text-center text-sm text-ed-muted"
              >
                Esta propuesta no tiene artículos vinculados con el grado mínimo seleccionado.
              </p>
            </div>
          </div>
        </div>

        <div
          v-else
          key="browse"
          class="relative"
          :style="surfaceStyle"
        >
          <template v-if="grouping === 'linkCount'">
            <div
              v-for="(column, index) in columns"
              :key="`band-${column.key}`"
              class="pointer-events-none absolute inset-y-0 rounded-md border-2 border-ed-border"
              :class="index % 2 === 0 ? 'bg-ed-ink/5' : 'bg-ed-muted/5'"
              :style="{
                left: `${column.x - COLUMN_GAP / 2 + 8}px `,
                width: `${PROPOSAL_CARD_WIDTH + COLUMN_GAP - 12}px`
              }"
            />
            <div
              v-for="column in columns"
              :key="column.key"
              class="absolute top-4 flex items-center gap-2 text-11 font-semibold tracking-widest text-ed-muted uppercase"
              :style="{
                left: `${column.x}px`,
                width: `${PROPOSAL_CARD_WIDTH}px`
              }"
            >
              {{ column.label }}
              <span class="inline-flex h-4.5 items-center rounded bg-ed-ink/8 px-1.5 text-2xs font-semibold tracking-wide text-ed-ink">
                {{ column.proposals.length }}
              </span>
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
            class="absolute inset-x-0 top-24 px-8 text-center text-sm text-ed-muted"
          >
            {{ emptyStateMessage }}
          </p>
        </div>
      </Transition>
    </div>
  </section>
</template>
