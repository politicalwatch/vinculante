<script setup lang="ts">
import {
  PROPOSAL_CARD_HEIGHT,
  PROPOSAL_CARD_WIDTH,
  type EditorialProposal
} from '~/composables/useEditorialBoard'

const props = defineProps<{
  proposal: EditorialProposal
}>()

/**
 * The outer element owns the position transform so the fly-to-column transition
 * never competes with the idle float animation running on the inner element.
 */
const positionStyle = computed(() => ({
  width: `${PROPOSAL_CARD_WIDTH}px`,
  height: `${PROPOSAL_CARD_HEIGHT}px`,
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
        class="proposal-card"
        :class="[
          props.proposal.accentSide === 'left' ? 'accent-left' : 'accent-right',
          props.proposal.stacked ? 'is-stacked' : ''
        ]"
      >
        <div class="flex items-baseline justify-between gap-4">
          <span
            class="text-[10px] font-semibold tracking-[0.06em] whitespace-nowrap shrink-0"
            :class="props.proposal.accentSide === 'left'
              ? 'text-(--ed-ink)'
              : 'text-(--ed-accent)'"
          >
            {{ props.proposal.label }}
          </span>
          <span class="text-[10px] text-(--ed-muted) whitespace-nowrap truncate">
            {{ props.proposal.relationLabel }}
          </span>
        </div>
        <p class="mt-2.5 text-[13px] leading-[1.55] text-(--ed-body) line-clamp-3">
          {{ props.proposal.text }}
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
  transition: box-shadow 0.3s ease;
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
