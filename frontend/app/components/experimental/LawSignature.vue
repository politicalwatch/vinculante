<script setup lang="ts">
const GOLDEN = 2.399963229728653

const props = withDefaults(defineProps<{
  articles: number
  touched: number
  proposals: number
  incorporated: number
  size?: number
  maxProposals?: number
  accent?: string
}>(), {
  size: 112,
  maxProposals: 1,
  accent: 'var(--ed-accent)'
})

const signatureStyle = computed(() => ({
  '--sig-accent': props.accent
} as Record<string, string>))

function clamp(value: number, lo: number, hi: number) {
  return Math.max(lo, Math.min(hi, value))
}

function areaScale(value: number, max: number, lo: number, hi: number) {
  const t = clamp(max > 0 ? value / max : 0, 0, 1)
  return lo + Math.sqrt(t) * (hi - lo)
}

const geometry = computed(() => {
  const { size } = props
  const cx = size / 2
  const cy = size / 2
  const rMax = size / 2 - 1
  const r0 = rMax * 0.66
  const tickLen = rMax * 0.16
  const articles = Math.max(0, Math.round(props.articles))
  const touched = clamp(Math.round(props.touched), 0, articles)
  const proposals = Math.max(0, Math.round(props.proposals))
  const incorporated = clamp(Math.round(props.incorporated), 0, proposals)
  const maxProposals = Math.max(props.maxProposals, 1)

  const tickWidth = articles > 0
    ? clamp(((2 * Math.PI * r0) / articles) * 0.55, 0.45, 3.2)
    : 0

  const ticks = Array.from({ length: articles }, (_, i) => {
    const th = -Math.PI / 2 + (2 * Math.PI * i) / articles
    return {
      x1: cx + Math.cos(th) * r0,
      y1: cy + Math.sin(th) * r0,
      x2: cx + Math.cos(th) * (r0 + tickLen),
      y2: cy + Math.sin(th) * (r0 + tickLen),
      reached: i < touched
    }
  })

  const maxR = rMax * 0.54
  const field = areaScale(proposals, maxProposals, maxR * 0.34, maxR)
  const dotR = proposals > 0
    ? clamp((field / Math.sqrt(proposals)) * 0.54, 0.45, 3)
    : 0

  const dots = Array.from({ length: proposals }, (_, k) => {
    const r = field * Math.sqrt((k + 0.5) / proposals)
    const th = k * GOLDEN
    return {
      cx: cx + Math.cos(th) * r,
      cy: cy + Math.sin(th) * r,
      r: dotR,
      filled: k < incorporated,
      strokeWidth: clamp(dotR * 0.55, 0.35, 0.8)
    }
  })

  return { ticks, dots, tickWidth }
})

const label = computed(() =>
  `${props.articles} artículos, ${props.touched} con propuestas, ${props.proposals} propuestas, ${props.incorporated} incorporadas`
)
</script>

<template>
  <svg
    :width="size"
    :height="size"
    :viewBox="`0 0 ${size} ${size}`"
    role="img"
    :aria-label="label"
    class="pointer-events-none"
    :style="signatureStyle"
  >
    <line
      v-for="(tick, i) in geometry.ticks"
      :key="`tick-${i}`"
      :x1="tick.x1"
      :y1="tick.y1"
      :x2="tick.x2"
      :y2="tick.y2"
      :stroke="tick.reached ? 'var(--sig-accent)' : 'var(--ed-shape-empty)'"
      :stroke-opacity="tick.reached ? 1 : 0.7"
      :stroke-width="geometry.tickWidth"
      stroke-linecap="round"
    />
    <circle
      v-for="(dot, k) in geometry.dots"
      :key="`dot-${k}`"
      :cx="dot.cx"
      :cy="dot.cy"
      :r="dot.r"
      :fill="dot.filled ? 'var(--sig-accent)' : 'none'"
      :fill-opacity="dot.filled ? 0.85 : 0"
      :stroke="dot.filled ? 'none' : 'var(--sig-accent)'"
      :stroke-opacity="dot.filled ? 1 : 0.45"
      :stroke-width="dot.filled ? 0 : dot.strokeWidth"
    />
  </svg>
</template>
