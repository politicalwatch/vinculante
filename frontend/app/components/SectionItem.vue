<script setup lang="ts">
import type { Section } from '~/types/api'
import { highlightQuotes, removeHighlights } from '~/utils/highlight'

const props = defineProps<{
  section: Section
  depth: number
  active: boolean
  spans?: [number, number][]
  matchCount?: number
}>()

defineEmits<{ click: [] }>()

const contentRef = ref<HTMLElement | null>(null)

const quotes = computed(() =>
  (props.spans ?? []).map(([s, e]) => props.section.text.slice(s, e)).filter(q => q.length >= 5)
)

watch(
  [quotes, contentRef],
  ([qs, el]) => {
    if (!el) return
    removeHighlights(el)
    if (qs.length) {
      nextTick(() => { if (el) highlightQuotes(el, qs) })
    }
  },
  { immediate: true }
)
</script>

<template>
  <div
    v-if="!section.is_matchable"
    class="px-4 py-3 border-b border-default bg-elevated/40 select-none"
    :style="{ paddingLeft: `${16 + depth * 16}px` }"
  >
    <div
      class="text-default font-semibold uppercase tracking-wide text-xs prose prose-sm dark:prose-invert max-w-none
             [&_h1]:!text-base [&_h2]:!text-sm [&_h3]:!text-xs [&_h4]:!text-xs
             [&_h1]:!font-semibold [&_h2]:!font-semibold [&_h3]:!font-semibold [&_h4]:!font-semibold
             [&_h1]:!my-0 [&_h2]:!my-0 [&_h3]:!my-0 [&_h4]:!my-0
             [&_h1]:!uppercase [&_h2]:!uppercase [&_h3]:!uppercase [&_h4]:!uppercase
             [&_h1]:!tracking-wide [&_h2]:!tracking-wide [&_h3]:!tracking-wide [&_h4]:!tracking-wide"
    >
      <MDC v-if="section.text_markdown" :value="section.text_markdown" />
      <span v-else>{{ section.text }}</span>
    </div>
  </div>

  <button
    v-else
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
      class="absolute top-3 right-3 font-bold font-mono rounded-full"
    >
      {{ matchCount }}
    </UBadge>
    <div v-if="section.section_number" class="text-xs text-muted mb-4 font-light uppercase tracking-wide">
      {{ section.section_number }}
    </div>
    <div
      ref="contentRef"
      class="text-sm text-default pr-10 prose prose-sm dark:prose-invert max-w-none
             [&_h1]:!text-2xl [&_h2]:!text-xl [&_h3]:!text-lg [&_h4]:!text-base [&_h5]:!text-sm [&_h6]:!text-sm
             [&_h1]:!font-semibold [&_h2]:!font-semibold [&_h3]:!font-semibold [&_h4]:!font-semibold
             [&_h1]:!mt-0 [&_h2]:!mt-0 [&_h3]:!mt-0 [&_h4]:!mt-0
             [&_h1]:!mb-6 [&_h2]:!mb-4 [&_h3]:!mb-2 [&_h4]:!mb-1
             [&_p]:!my-1 [&_p]:!leading-relaxed [&_ul]:!my-2 [&_ol]:!my-2 [&_li]:!my-2 [&_li]:!leading-relaxed"
    >
      <MDC v-if="section.text_markdown" :value="section.text_markdown" />
      <p v-else class="whitespace-pre-line">{{ section.text }}</p>
    </div>
  </button>
</template>
