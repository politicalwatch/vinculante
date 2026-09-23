<script setup lang="ts">
import { useResizeObserver } from '@vueuse/core'
import {
  PROPOSAL_CARD_HEIGHT,
  PROPOSAL_CARD_WIDTH,
  type EditorialProposal
} from '~/composables/useEditorialBoard'

const props = defineProps<{
  proposal: EditorialProposal
  /** Double the width while expanded; the board clamps it to the surface. */
  wideWhenExpanded?: boolean
  selectedArticleId?: number | null
}>()

const emit = defineEmits<{
  toggle: []
  measure: [height: number]
  selectArticle: [sectionId: number]
}>()

const tagClass = computed(() =>
  props.proposal.accentSide === 'left'
    ? 'text-(--ed-ink) border-(--ed-ink)/30'
    : 'text-(--ed-accent) border-(--ed-accent)/40'
)

const showLinkedArticles = computed(() =>
  props.proposal.expanded && (props.proposal.linkedArticles?.length ?? 0) > 0
)

const card = ref<HTMLElement | null>(null)

/** The expanded height is unknowable up front, so report it back for stack layout. */
useResizeObserver(card, (entries) => {
  const el = entries[0]?.target
  if (!props.proposal.expanded || !(el instanceof HTMLElement)) return
  emit('measure', el.offsetHeight)
})

/**
 * The outer element owns the position transform so the fly-to-column transition
 * never competes with the idle float animation running on the inner element.
 */
const positionStyle = computed(() => ({
  width: props.wideWhenExpanded && props.proposal.expanded
    ? `${PROPOSAL_CARD_WIDTH * 2}px`
    : `${PROPOSAL_CARD_WIDTH}px`,
  maxWidth: `calc(100% - ${props.proposal.x}px)`,
  height: props.proposal.expanded ? 'auto' : `${PROPOSAL_CARD_HEIGHT}px`,
  transform: `translate3d(${props.proposal.x}px, ${props.proposal.y}px, 0)`,
  opacity: props.proposal.opacity,
  zIndex: props.proposal.zIndex,
  pointerEvents: props.proposal.opacity === 0 ? ('none' as const) : ('auto' as const)
}))

const floatStyle = computed(() => ({
  '--float-duration': `${props.proposal.floatDuration}s`,
  '--float-delay': `${props.proposal.floatDelay}s`,
  '--float-x': `${props.proposal.floatX}px`,
  '--float-y': `${props.proposal.floatY}px`
}))
</script>

<template>
  <div
    class="proposal-position"
    :data-proposal-id="props.proposal.proposalId"
    :style="positionStyle"
    :aria-hidden="props.proposal.opacity === 0"
  >
    <div
      class="proposal-float"
      :class="props.proposal.floating ? 'is-floating' : ''"
      :style="floatStyle"
    >
      <article
        ref="card"
        class="proposal-card"
        :class="[
          props.proposal.accentSide === 'left' ? 'accent-left' : 'accent-right',
          props.proposal.stacked ? 'is-stacked' : '',
          props.proposal.expanded ? 'is-expanded' : ''
        ]"
        role="button"
        tabindex="0"
        :aria-expanded="props.proposal.expanded"
        @click.stop="emit('toggle')"
        @keydown.enter.prevent="emit('toggle')"
        @keydown.space.prevent="emit('toggle')"
      >
        <div class="flex items-center justify-between gap-3">
          <span class="flex items-center gap-1.5 min-w-0">
            <span
              v-if="props.proposal.authorTypeLabel"
              class="proposal-tag shrink-0"
              :class="tagClass"
            >
              {{ props.proposal.authorTypeLabel }}
            </span>
            <span
              v-if="props.proposal.topic"
              class="proposal-tag truncate text-(--ed-muted) border-(--ed-border)"
              :title="props.proposal.topic"
            >
              {{ props.proposal.topic }}
            </span>
          </span>
          <span class="flex items-center gap-1 min-w-0 shrink-0 text-[10px] text-(--ed-muted)">
            <span class="whitespace-nowrap truncate">{{ props.proposal.relationLabel }}</span>
            <UIcon
              :name="props.proposal.expanded ? 'i-lucide-chevron-up' : 'i-lucide-chevron-down'"
              class="size-3 shrink-0"
            />
          </span>
        </div>
        <p
          class="mt-2.5 text-[13px] leading-[1.55]"
          :class="props.proposal.expanded
            ? 'whitespace-pre-line text-(--ed-body)'
            : 'line-clamp-3 proposal-clamp'"
        >
          <span class="text-(--ed-body) font-normal">{{ props.proposal.text }}</span>
        </p>

        <section
          v-if="showLinkedArticles"
          class="proposal-section"
        >
          <h4 class="proposal-section-title">
            Artículos vinculados
          </h4>
          <ul class="flex flex-col gap-1">
            <li
              v-for="article in props.proposal.linkedArticles"
              :key="article.sectionId"
            >
              <button
                type="button"
                class="linked-article"
                :class="article.sectionId === props.selectedArticleId ? 'is-selected' : ''"
                :aria-pressed="article.sectionId === props.selectedArticleId"
                @click.stop="emit('selectArticle', article.sectionId)"
                @keydown.stop
              >
                
                <span class="text-sm leading-snug text-(--ed-ink) truncate">
                  {{ article.title }}
                </span>
                <UIcon
                  name="i-lucide-chevron-right"
                  class="size-4 shrink-0"
                />
              </button>
            </li>
          </ul>
        </section>

        <section
          v-if="props.proposal.expanded && props.proposal.explanation"
          class="proposal-section"
        >
          <h4 class="proposal-section-title">
            <HelpTooltip
              label="Ayuda: Razonamiento de la vinculación"
              text="El razonamiento de la vinculación es el texto que explica la relación entre la propuesta y el artículo."
            />
            Razonamiento de la vinculación
          </h4>
          <p class="text-[12px] leading-relaxed text-(--ed-body) whitespace-pre-line">
            {{ props.proposal.explanation }}
          </p>
        </section>
      </article>
    </div>
  </div>
</template>

<style scoped>
.proposal-position {
  position: absolute;
  top: 0;
  left: 0;
  transition:
    transform 0.7s cubic-bezier(0.22, 1, 0.36, 1),
    opacity 0.4s ease;
  will-change: transform;
}

.proposal-float {
  width: 100%;
  height: 100%;
}

.proposal-float.is-floating {
  animation: editorial-float var(--float-duration) ease-in-out var(--float-delay) infinite alternate;
}

.proposal-card {
  position: relative;
  height: 100%;
  overflow: hidden;
  padding: 16px;
  background: var(--ed-surface);
  border: 1px solid var(--ed-border);
  border-radius: 4px;
  box-shadow: 0 2px 6px rgb(27 58 92 / 0.07);
  transition:
    box-shadow 0.3s ease,
    border-color 0.3s ease;
  cursor: pointer;
}

.proposal-card:hover:not(.is-expanded) {
  border-color: rgb(27 58 92 / 0.22);
  box-shadow: 0 8px 22px rgb(27 58 92 / 0.16);
}

/* The truncation ellipsis takes the clamped block's color and weight, not the inner text's. */
.proposal-clamp {
  color: var(--ed-accent);
  font-weight: 800;
}

.proposal-tag {
  display: inline-flex;
  align-items: center;
  height: 18px;
  padding: 0 6px;
  border-width: 1px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.04em;
  white-space: nowrap;
}

.proposal-section {
  margin-top: 14px;
  padding-top: 12px;
  border-top: 1px solid var(--ed-border);
}

.proposal-section-title {
  margin-bottom: 8px;
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--ed-muted);
}

.linked-article {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  min-width: 0;
  padding: 6px 8px;
  border-radius: 4px;
  text-align: left;
  cursor: pointer;
  transition: background 0.15s ease;
}

.linked-article:hover {
  background: color-mix(in oklab, var(--ed-ink) 6%, transparent);
}

.linked-article.is-selected {
  background: color-mix(in oklab, var(--ed-accent) 12%, transparent);
}

.linked-article:focus-visible {
  outline: 2px solid var(--ed-accent);
  outline-offset: 1px;
}

.proposal-card:focus-visible {
  outline: 2px solid var(--ed-accent);
  outline-offset: 2px;
}

/* Grow to the full text, capped so a long proposal scrolls inside its own card. */
.proposal-card.is-expanded {
  height: auto;
  max-height: min(60vh, 460px);
  overflow-y: auto;
  overscroll-behavior: contain;
  box-shadow: 0 10px 28px rgb(27 58 92 / 0.18);
}

.proposal-card.is-stacked {
  box-shadow: 0 4px 14px rgb(27 58 92 / 0.12);
}

.proposal-card::before {
  content: '';
  position: absolute;
  top: 0;
  bottom: 0;
  width: 4px;
}

.proposal-card.accent-left::before {
  left: 0;
  background: var(--ed-ink);
}

.proposal-card.accent-right::before {
  right: 0;
  background: var(--ed-accent);
}

.proposal-card.accent-left {
  padding-left: 20px;
}

.proposal-card.accent-right {
  padding-right: 20px;
}

@keyframes editorial-float {
  from {
    transform: translate3d(0, 0, 0);
  }
  to {
    transform: translate3d(var(--float-x), var(--float-y), 0);
  }
}

@media (prefers-reduced-motion: reduce) {
  .proposal-position {
    transition: opacity 0.2s ease;
  }

  .proposal-float.is-floating {
    animation: none;
  }
}
</style>
