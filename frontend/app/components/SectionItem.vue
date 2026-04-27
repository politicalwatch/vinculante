<script setup lang="ts">
import type { Section } from '~/types/api'

const props = defineProps<{
  section: Section
  depth: number
  active: boolean
  spans?: [number, number][]
  matchCount?: number
}>()

defineEmits<{ click: [] }>()

const segments = computed(() => {
  const text = props.section.text
  const spans = props.spans ?? []
  if (!spans.length) return [{ text, hl: false }]

  const sorted = [...spans]
    .map(([s, e]) => [Math.max(0, s), Math.min(text.length, e)] as const)
    .filter(([s, e]) => e > s)
    .sort((a, b) => a[0] - b[0])

  const merged: [number, number][] = []
  for (const [s, e] of sorted) {
    const last = merged[merged.length - 1]
    if (last && s <= last[1]) last[1] = Math.max(last[1], e)
    else merged.push([s, e])
  }

  const out: { text: string, hl: boolean }[] = []
  let i = 0
  for (const [s, e] of merged) {
    if (s > i) out.push({ text: text.slice(i, s), hl: false })
    out.push({ text: text.slice(s, e), hl: true })
    i = e
  }
  if (i < text.length) out.push({ text: text.slice(i), hl: false })
  return out
})
</script>

<template>
  <button
    class="w-full text-left px-4 py-3 border-b border-default transition-colors hover:bg-elevated relative"
    :class="active ? 'bg-primary/10 border-l-2 border-l-primary' : ''"
    :style="{ paddingLeft: `${16 + depth * 16}px` }"
    @click="$emit('click')"
  >
    <UBadge
      v-if="matchCount && matchCount > 0"
      :color="active ? 'primary' : 'neutral'"
      variant="subtle"
      size="md"
      class="absolute top-3 right-3 font-bold  font-mono rounded-full"
    >
      {{ matchCount }}
    </UBadge>
    <div v-if="section.section_number || section.section_type" class="text-xs text-muted mb-0.5 font-medium uppercase tracking-wide">
      {{ [section.section_number, section.section_type].filter(Boolean).join(' · ') }}
    </div>
    <p class="text-sm text-default whitespace-pre-line pr-10">
      <template v-for="(seg, i) in segments" :key="i">
        <mark
          v-if="seg.hl"
          class="bg-yellow-200 dark:bg-yellow-500/30 text-inherit rounded-sm p-0"
        >{{ seg.text }}</mark>
        <span v-else>{{ seg.text }}</span>
      </template>
    </p>
  </button>
</template>
