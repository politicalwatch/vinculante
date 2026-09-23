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
  /** Sit in normal flow instead of the absolute board layer. */
  inFlow?: boolean
  selectedArticleId?: number | null
}>()

const emit = defineEmits<{
  toggle: []
  measure: [height: number]
  selectArticle: [sectionId: number]
}>()

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

const REVEAL_PAD = 24

function scrollParent(el: HTMLElement): HTMLElement | null {
  let node = el.parentElement
  while (node) {
    const { overflowX, overflowY } = getComputedStyle(node)
    if (/(auto|scroll)/.test(`${overflowX}${overflowY}`)) return node
    node = node.parentElement
  }
  return null
}

/** Nudge the board scroll the minimum amount that puts the whole card inside the viewport. */
function revealCard() {
  const box = card.value?.closest('.proposal-position')
  if (!(box instanceof HTMLElement)) return
  const layer = scrollParent(box)
  if (!layer) return

  const boxRect = box.getBoundingClientRect()
  const view = layer.getBoundingClientRect()
  const left = boxRect.left - view.left + layer.scrollLeft
  const top = boxRect.top - view.top + layer.scrollTop

  let nextLeft = layer.scrollLeft
  let nextTop = layer.scrollTop

  if (boxRect.width + REVEAL_PAD * 2 >= layer.clientWidth) {
    nextLeft = left - REVEAL_PAD
  } else if (left < layer.scrollLeft + REVEAL_PAD) {
    nextLeft = left - REVEAL_PAD
  } else if (left + boxRect.width > layer.scrollLeft + layer.clientWidth - REVEAL_PAD) {
    nextLeft = left + boxRect.width - layer.clientWidth + REVEAL_PAD
  }

  if (boxRect.height + REVEAL_PAD * 2 >= layer.clientHeight) {
    nextTop = top - REVEAL_PAD
  } else if (top < layer.scrollTop + REVEAL_PAD) {
    nextTop = top - REVEAL_PAD
  } else if (top + boxRect.height > layer.scrollTop + layer.clientHeight - REVEAL_PAD) {
    nextTop = top + boxRect.height - layer.clientHeight + REVEAL_PAD
  }

  nextLeft = Math.min(Math.max(0, nextLeft), Math.max(0, layer.scrollWidth - layer.clientWidth))
  nextTop = Math.min(Math.max(0, nextTop), Math.max(0, layer.scrollHeight - layer.clientHeight))
  if (Math.abs(nextLeft - layer.scrollLeft) < 1 && Math.abs(nextTop - layer.scrollTop) < 1) return

  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  layer.scrollTo({
    left: nextLeft,
    top: nextTop,
    behavior: reduceMotion ? 'auto' : 'smooth'
  })
}

watch(() => props.proposal.expanded, async () => {
  if (props.inFlow || props.proposal.stacked || props.proposal.opacity === 0) return
  await nextTick()
  revealCard()
})

const cardShadow = computed(() => {
  if (props.proposal.expanded) return 'shadow-lg'
  if (props.proposal.stacked) return 'shadow-md'
  return 'shadow-sm hover:border-ed-ink/20 hover:shadow-md'
})
</script>

<template>
  <div
    class="proposal-position top-0 left-0 will-change-transform"
    :class="props.inFlow ? 'relative w-full' : 'absolute'"
    :data-proposal-id="props.proposal.proposalId"
    :style="positionStyle"
    :aria-hidden="props.proposal.opacity === 0"
  >
    <div
      class="proposal-float size-full"
      :class="props.proposal.floating ? 'is-floating' : ''"
      :style="floatStyle"
    >
      <article
        ref="card"
        class="proposal-card relative h-full cursor-pointer overflow-hidden rounded border border-ed-border bg-ed-surface p-4 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ed-accent"
        :class="[
          cardShadow,
          props.proposal.accentSide === 'left' ? 'pl-5' : 'pr-5',
          props.proposal.expanded ? 'is-expanded h-auto overflow-y-auto overscroll-contain' : ''
        ]"
        role="button"
        tabindex="0"
        :aria-expanded="props.proposal.expanded"
        @click.stop="emit('toggle')"
        @keydown.enter.prevent="emit('toggle')"
        @keydown.space.prevent="emit('toggle')"
      >
        <span
          class="pointer-events-none absolute inset-y-0 w-1"
          :class="props.proposal.accentSide === 'left' ? 'left-0 bg-ed-ink' : 'right-0 bg-ed-accent'"
          aria-hidden="true"
        />

        <div class="flex items-center justify-between gap-3">
          <span class="flex items-center gap-1.5 min-w-0">
            <span
              v-if="props.proposal.authorTypeLabel"
              class="inline-flex h-4.5 shrink-0 items-center rounded border px-1.5 text-2xs font-semibold tracking-wide whitespace-nowrap"
              :class="props.proposal.accentSide === 'left'
                ? 'border-ed-ink/30 text-ed-ink'
                : 'border-ed-accent/40 text-ed-accent'"
            >
              {{ props.proposal.authorTypeLabel }}
            </span>
            <span
              v-if="props.proposal.topic"
              class="inline-flex h-4.5 min-w-0 items-center truncate rounded border border-ed-border px-1.5 text-2xs font-semibold tracking-wide whitespace-nowrap text-ed-muted"
              :title="props.proposal.topic"
            >
              {{ props.proposal.topic }}
            </span>
          </span>
          <span class="flex items-center gap-1 min-w-0 shrink-0 text-2xs text-ed-muted">
            <span class="whitespace-nowrap truncate">{{ props.proposal.relationLabel }}</span>
            <UIcon
              :name="props.proposal.expanded ? 'i-lucide-chevron-up' : 'i-lucide-chevron-down'"
              class="size-3 shrink-0"
            />
          </span>
        </div>
        <p
          class="mt-2.5 text-13"
          :class="props.proposal.expanded
            ? 'whitespace-pre-line text-ed-body'
            : 'line-clamp-3 font-extrabold text-ed-accent'"
        >
          <span class="font-normal text-ed-body">{{ props.proposal.text }}</span>
        </p>

        <section
          v-if="showLinkedArticles"
          class="mt-3.5 border-t border-ed-border pt-3"
        >
          <h4 class="mb-2 text-2xs font-semibold tracking-widest text-ed-muted uppercase">
            Artículos vinculados
          </h4>
          <ul class="flex flex-col gap-1">
            <li
              v-for="article in props.proposal.linkedArticles"
              :key="article.sectionId"
            >
              <button
                type="button"
                class="flex w-full min-w-0 cursor-pointer items-center gap-2.5 rounded px-2 py-1.5 text-left transition-colors hover:bg-ed-ink/6 focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-ed-accent"
                :class="article.sectionId === props.selectedArticleId ? 'bg-ed-accent/12' : ''"
                :aria-pressed="article.sectionId === props.selectedArticleId"
                @click.stop="emit('selectArticle', article.sectionId)"
                @keydown.stop
              >
                <span class="truncate text-sm leading-snug text-ed-ink">
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
          class="mt-3.5 border-t border-ed-border pt-3"
        >
          <h4 class="mb-2 text-2xs font-semibold tracking-widest text-ed-muted uppercase">
            <HelpTooltip
              label="Ayuda: Razonamiento de la vinculación"
              text="El razonamiento de la vinculación es el texto que explica la relación entre la propuesta y el artículo."
            />
            Razonamiento de la vinculación
          </h4>
          <p class="text-xs leading-relaxed text-ed-body whitespace-pre-line">
            {{ props.proposal.explanation }}
          </p>
        </section>
      </article>
    </div>
  </div>
</template>

<style scoped>
.proposal-position {
  transition:
    transform 0.7s cubic-bezier(0.22, 1, 0.36, 1),
    opacity 0.4s ease;
}

.proposal-float.is-floating {
  animation: editorial-float var(--float-duration) ease-in-out var(--float-delay) infinite alternate;
}

/* Grow to the full text, capped so a long proposal scrolls inside its own card. */
.proposal-card.is-expanded {
  max-height: min(60vh, 28rem);
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
