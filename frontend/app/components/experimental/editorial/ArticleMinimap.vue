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

function shapeFill(article: EditorialArticle): string | undefined {
  if (article.sectionId === props.selectedArticleId) return undefined
  const mix = Math.round(article.linkRatio * 100)
  return `color-mix(in oklab, var(--color-ed-accent) ${mix}%, var(--color-ed-shape-empty))`
}
</script>

<template>
  <div
    ref="root"
    class="flex w-14 shrink-0 flex-col items-center gap-2 overflow-y-auto overscroll-contain border-r border-ed-border bg-ed-surface-sunken py-4"
  >
    <span class="shrink-0 text-3xs font-semibold tracking-widest text-ed-muted">
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
        class="cursor-pointer rounded-sm transition-all hover:brightness-95"
        :class="article.sectionId === props.selectedArticleId
          ? 'bg-ed-ink ring-1 ring-ed-ink ring-offset-2'
          : ''"
        :style="{
          width: `${article.minimapWidth}px`,
          height: `${article.minimapHeight}px`,
          background: shapeFill(article)
        }"
        :title="shapeTitle(article)"
        :aria-label="shapeTitle(article)"
        @click="emit('select', article.sectionId)"
      />
    </div>

    <span class="shrink-0 text-3xs font-semibold tracking-widest text-ed-muted">
      END
    </span>
  </div>
</template>
