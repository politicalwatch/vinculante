<script setup lang="ts">
import { MINIMAP_CONFIG, type EditorialArticle } from '~/composables/useEditorialBoard'

const props = defineProps<{
  articles: EditorialArticle[]
  selectedArticleId: number | null
  /** 0–1 scroll progress of the article column, mirrored so both stay in register. */
  scrollRatio: number
}>()

const emit = defineEmits<{
  select: [sectionId: number]
}>()

const root = ref<HTMLElement | null>(null)

watch(
  () => props.scrollRatio,
  (ratio) => {
    const el = root.value
    if (!el) return
    const scrollable = el.scrollHeight - el.clientHeight
    if (scrollable <= 0) return
    el.scrollTop = ratio * scrollable
  }
)

/**
 * Article shapes grow rightwards, so the strip must be wide enough for the
 * widest possible rect regardless of the current data.
 */
const stripWidth = computed(
  () => MINIMAP_CONFIG.baseWidth * MINIMAP_CONFIG.maxWidthFactor
)

function shapeTitle(article: EditorialArticle): string {
  const links = article.linkCount === 1
    ? '1 vinculación'
    : `${article.linkCount} vinculaciones`
  return `${article.label} · ${links} · ${article.wordCount} palabras`
}
</script>

<template>
  <div
    ref="root"
    class="editorial-minimap shrink-0 flex flex-col items-center gap-2 py-4 overflow-y-auto overscroll-contain"
  >
    <span class="text-[9px] font-semibold tracking-widest text-(--ed-muted) shrink-0">
      DOC
    </span>

    <div
      class="flex flex-col items-start"
      :style="{ width: `${stripWidth}px`, gap: `${MINIMAP_CONFIG.gap}px` }"
    >
      <button
        v-for="article in props.articles"
        :key="article.sectionId"
        type="button"
        class="minimap-shape"
        :class="article.sectionId === props.selectedArticleId ? 'is-selected' : ''"
        :style="{
          'width': `${article.minimapWidth}px`,
          'height': `${article.minimapHeight}px`,
          '--shape-mix': `${Math.round(article.linkRatio * 100)}%`
        }"
        :title="shapeTitle(article)"
        :aria-label="shapeTitle(article)"
        @click="emit('select', article.sectionId)"
      />
    </div>

    <span class="text-[9px] font-semibold tracking-widest text-(--ed-muted) shrink-0">
      END
    </span>
  </div>
</template>

<style scoped>
.editorial-minimap {
  width: 56px;
  border-right: 1px solid var(--ed-border);
  background: var(--ed-surface-sunken);
}

.minimap-shape {
  border-radius: 2px;
  background: color-mix(in oklab, var(--ed-accent) var(--shape-mix), var(--ed-shape-empty));
  transition:
    width 0.3s cubic-bezier(0.22, 1, 0.36, 1),
    outline-color 0.2s ease,
    opacity 0.2s ease;
  outline: 1px solid transparent;
  outline-offset: 2px;
  cursor: pointer;
}

.minimap-shape:hover {
  opacity: 0.75;
}

.minimap-shape.is-selected {
  background: var(--ed-ink);
  outline-color: var(--ed-ink);
}
</style>
