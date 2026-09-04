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
    WebkitBoxOrient: 'vertical',
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
      class="prose-paragraph"
      :style="clampStyle(index)"
    >
      {{ paragraph }}
    </p>

    <slot name="lead" />

    <template v-if="expanded">
      <p
        v-for="(paragraph, index) in rest"
        :key="`rest-${index}`"
        class="prose-paragraph"
      >
        {{ paragraph }}
      </p>

      <slot name="extra" />
    </template>

    <button
      v-if="hasMore"
      type="button"
      class="toggle"
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

<style scoped>
.prose-paragraph {
  font-size: 16px;
  line-height: 1.6;
  color: var(--ed-ink);
}

.toggle {
  align-self: flex-start;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 700;
  color: var(--ed-accent);
  cursor: pointer;
}

.toggle:hover {
  text-decoration: underline;
}
</style>
