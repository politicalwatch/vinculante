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

// ---------------------------------------------------------------------------
// Non-matchable: header vs prose discrimination
// ---------------------------------------------------------------------------

const HEADER_TYPES = new Set(['titulo', 'capitulo', 'seccion'])

const isHeaderStyle = computed(() =>
  !props.section.is_matchable && HEADER_TYPES.has(props.section.section_type ?? '')
)
const isProseStyle = computed(() =>
  !props.section.is_matchable && !HEADER_TYPES.has(props.section.section_type ?? '')
)

// ---------------------------------------------------------------------------
// Prose label
// ---------------------------------------------------------------------------

const TYPE_LABELS: Record<string, string> = {
  preambulo: 'Preámbulo',
  exposicion_motivos: 'Exposición de motivos',
  disp_adicional: 'Disposición adicional',
  disp_transitoria: 'Disposición transitoria',
  disp_derogatoria: 'Disposición derogatoria',
  disp_final: 'Disposición final',
}

const sectionType = computed(() => props.section.section_type ?? '')
const sectionNumber = computed(() => props.section.section_number ?? '')

const proseLabel = computed(() => {
  const base = TYPE_LABELS[sectionType.value] ?? sectionType.value
  if (sectionNumber.value && sectionType.value.startsWith('disp_')) {
    // section_number for disp_* is e.g. "final primera" — keep only the ordinal
    const ord = sectionNumber.value.split(' ').slice(1).join(' ')
    return ord ? `${base} ${ord}` : base
  }
  if (sectionNumber.value) return `${base} ${sectionNumber.value}`
  return base
})

// ---------------------------------------------------------------------------
// Prose collapse
// ---------------------------------------------------------------------------

const proseRef = ref<HTMLElement | null>(null)
const expanded = ref(false)
const overflowing = ref(false)
const contentHeight = ref(0)

let observer: ResizeObserver | null = null

function checkOverflow() {
  const el = proseRef.value
  if (!el) return
  // scrollHeight is always the full natural height, even when max-height clamps it.
  // We use this to drive the CSS transition so it animates between two numeric values
  // (contentHeight px ↔ 4.5rem) instead of the non-animatable max-height:none.
  contentHeight.value = el.scrollHeight
  if (!expanded.value) {
    overflowing.value = el.scrollHeight > el.clientHeight + 1
  }
}

onMounted(() => {
  observer = new ResizeObserver(checkOverflow)
  if (proseRef.value) observer.observe(proseRef.value)
  nextTick(checkOverflow)
})

onBeforeUnmount(() => {
  observer?.disconnect()
})

watch(
  () => props.section.text_markdown ?? props.section.text,
  () => {
    expanded.value = false
    nextTick(checkOverflow)
  }
)
</script>

<template>
  <!-- Non-matchable: short structural header (TÍTULO / CAPÍTULO / SECCIÓN) -->
  <div
    v-if="isHeaderStyle"
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
      <MDC
        v-if="section.text_markdown"
        :value="section.text_markdown"
      />
      <span v-else>{{ section.text }}</span>
    </div>
  </div>

  <!-- Non-matchable: long-form prose (preámbulo, exposición, disposiciones) -->
  <div
    v-else-if="isProseStyle"
    class="px-4 py-3 border-b border-default bg-elevated/40 select-none"
    :style="{ paddingLeft: `${16 + depth * 16}px` }"
  >
    <div class="flex items-start justify-between gap-2 mb-2">
      <div class="text-xs text-muted font-semibold uppercase tracking-wide">
        {{ proseLabel }}
      </div>
      <UButton
        v-if="overflowing"
        variant="ghost"
        color="neutral"
        size="xs"
        class="-my-1 -mr-2 shrink-0"
        :trailing-icon="expanded ? 'i-lucide-chevron-up' : 'i-lucide-chevron-down'"
        @click="expanded = !expanded"
      >
        {{ expanded ? 'Mostrar menos' : 'Mostrar más' }}
      </UButton>
    </div>
    <div
      ref="proseRef"
      class="prose prose-sm dark:prose-invert max-w-none text-sm text-default overflow-hidden
             [&_h1]:!text-sm [&_h2]:!text-sm [&_h3]:!text-sm [&_h4]:!text-sm [&_h5]:!text-sm [&_h6]:!text-sm
             [&_h1]:!font-semibold [&_h2]:!font-semibold [&_h3]:!font-semibold [&_h4]:!font-medium [&_h5]:!font-medium [&_h6]:!font-medium
             [&_h1]:!mt-0 [&_h2]:!mt-0 [&_h3]:!mt-0 [&_h4]:!mt-0
             [&_h1]:!mb-1 [&_h2]:!mb-1 [&_h3]:!mb-1 [&_h4]:!mb-1
             [&_p]:!my-1 [&_p]:!leading-relaxed [&_ul]:!my-1 [&_ol]:!my-1 [&_li]:!my-0.5"
      :class="!expanded && overflowing ? 'mask-[linear-gradient(to_bottom,black_60%,transparent)]' : ''"
      :style="{
        maxHeight: expanded && contentHeight ? `${contentHeight}px` : '4.5rem',
        transition: 'max-height 300ms cubic-bezier(0.4,0,0.2,1)'
      }"
    >
      <MDC
        v-if="section.text_markdown"
        :value="section.text_markdown"
      />
      <p
        v-else
        class="whitespace-pre-line"
      >
        {{ section.text }}
      </p>
    </div>
  </div>

  <!-- Matchable section -->
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
    <div
      v-if="section.section_number"
      class="text-xs text-muted mb-4 font-light uppercase tracking-wide"
    >
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
      <MDC
        v-if="section.text_markdown"
        :value="section.text_markdown"
      />
      <p
        v-else
        class="whitespace-pre-line"
      >
        {{ section.text }}
      </p>
    </div>
  </button>
</template>
