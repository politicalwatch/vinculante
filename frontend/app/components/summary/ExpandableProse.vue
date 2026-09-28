<script setup lang="ts">
const props = withDefaults(
  defineProps<{
    paragraphs: string[]
    /** Leading paragraphs kept visible while collapsed. */
    collapsedCount?: number
    /** Line clamp applied to the last always-visible paragraph while collapsed. */
    collapsedLines?: number
  }>(),
  { collapsedCount: 1, collapsedLines: undefined }
)

const slots = defineSlots<{
  /** Sits between the always-visible prose and the paragraphs revealed on expand. */
  lead?: () => unknown
  /** Revealed on expand, after the remaining paragraphs. */
  extra?: () => unknown
}>()

const expanded = ref(false)

const head = computed(() => props.paragraphs.slice(0, props.collapsedCount))
const rest = computed(() => props.paragraphs.slice(props.collapsedCount))

const hasMore = computed(() => rest.value.length > 0 || Boolean(slots.extra))

function clampStyle(index: number) {
  if (expanded.value || !props.collapsedLines || index !== head.value.length - 1) return undefined
  return {
    display: '-webkit-box',
    WebkitBoxOrient: 'vertical' as const,
    WebkitLineClamp: String(props.collapsedLines),
    overflow: 'hidden'
  }
}
</script>

<template>
  <div class="flex flex-col gap-3">
    <p
      v-for="(paragraph, index) in head"
      :key="`head-${index}`"
      class="text-base leading-relaxed text-ed-ink"
      :style="clampStyle(index)"
    >
      {{ paragraph }}
    </p>

    <slot name="lead" />

    <template v-if="expanded">
      <p
        v-for="(paragraph, index) in rest"
        :key="`rest-${index}`"
        class="text-base leading-relaxed text-ed-ink"
      >
        {{ paragraph }}
      </p>

      <slot name="extra" />
    </template>

    <button
      v-if="hasMore"
      type="button"
      class="inline-flex cursor-pointer items-center gap-2 self-start text-sm font-bold text-ed-accent hover:underline"
      :aria-expanded="expanded"
      @click="expanded = !expanded"
    >
      {{ expanded ? 'Leer menos' : '+ Leer más' }}
      <UIcon
        name="i-lucide-chevron-down"
        class="size-4 transition-transform"
        :class="expanded ? 'rotate-180' : ''"
      />
    </button>
  </div>
</template>
