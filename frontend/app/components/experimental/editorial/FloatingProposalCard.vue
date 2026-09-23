<script setup lang="ts">
import { useResizeObserver } from '@vueuse/core'
import {
  PROPOSAL_CARD_HEIGHT,
  PROPOSAL_CARD_WIDTH,
  type EditorialProposal
} from '~/composables/useEditorialBoard'

const props = defineProps<{
  proposal: EditorialProposal
}>()

const emit = defineEmits<{
  toggle: []
  measure: [height: number]
}>()

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
  width: `${PROPOSAL_CARD_WIDTH}px`,
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
        <div class="flex items-baseline justify-between gap-3">
          <span
            class="text-[10px] font-semibold tracking-[0.06em] whitespace-nowrap shrink-0"
            :class="props.proposal.accentSide === 'left'
              ? 'text-(--ed-ink)'
              : 'text-(--ed-accent)'"
          >
            {{ props.proposal.label }}
          </span>
          <span class="flex items-center gap-1 min-w-0 text-[10px] text-(--ed-muted)">
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
