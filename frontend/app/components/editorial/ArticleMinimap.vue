<script setup lang="ts">
import { useElementSize } from '@vueuse/core'
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

const X_PADDING = 4
const root = ref<HTMLElement | null>(null)
const track = ref<HTMLElement | null>(null)
const { width: trackWidth, height: trackHeight } = useElementSize(track)

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
 * One scale for every bar: fill the track, unless that would push the
 * tallest bar past the cap. Width uses the full track, keeping the 1×–3× range.
 */
const barLayout = computed(() => {
  const articles = props.articles
  const n = articles.length
  const width = trackWidth.value - X_PADDING * 2
  const height = trackHeight.value
  if (n === 0 || width <= 0 || height <= 0) {
    return articles.map(() => ({ width: 0, height: 0 }))
  }

  const { maxWidthFactor, maxHeight, gap } = MINIMAP_CONFIG
  const available = Math.max(0, height - (n - 1) * gap)
  const weights = articles.map(article => article.minimapHeight)
  const sum = weights.reduce((total, weight) => total + weight, 0)
  const tallest = Math.max(...weights)
  const scale = sum > 0 && tallest > 0
    ? Math.min(available / sum, maxHeight / tallest)
    : 0

  return articles.map((article, index) => ({
    width: width * (1 + article.linkRatio * (maxWidthFactor - 1)) / maxWidthFactor,
    height: weights[index]! * scale
  }))
})

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
    class="flex h-full min-h-0 w-20 shrink-0 flex-col items-center gap-2 overflow-y-auto overscroll-contain border-r border-ed-border bg-ed-surface-sunken py-4"
  >
    <span class="shrink-0 text-3xs font-semibold tracking-widest text-ed-muted">
      Articulado
      <HelpTooltip
        label="Ayuda sobre el minimapa de artículos">
        <p>El minimapa muestra el articulado de la ley y las vinculaciones detectadas entre las propuestas y los artículos.</p>
        <ul class="list-disc list-inside">
          <li>El largo de la barra indica el número de vinculaciones detectadas entre la propuesta y el artículo.</li>
          <li>El ancho de la barra indica el número de palabras del artículo.</li>
        </ul>
        <p>Por ejemplo una barra ancha y larga indica que ese artículo tiene muchas vinculaciones y es largo.</p>
        <p>Una barra estrecha y larga indica que hay muchas vinculaciones pero el artículo es corto.</p>
      </HelpTooltip>
      
    </span>

    <div
      ref="track"
      class="flex w-full min-h-0 flex-1 flex-col items-start px-2"
      :style="{ gap: `${MINIMAP_CONFIG.gap}px` }"
    >
      <button
        v-for="(article, index) in props.articles"
        :key="article.sectionId"
        type="button"
        class="cursor-pointer rounded-sm transition-all hover:brightness-95"
        :class="article.sectionId === props.selectedArticleId
          ? 'bg-ed-ink ring-1 ring-ed-ink ring-offset-2'
          : ''"
        :style="{
          width: `${barLayout[index]?.width ?? 0}px`,
          height: `${barLayout[index]?.height ?? 0}px`,
          background: shapeFill(article)
        }"
        :title="shapeTitle(article)"
        :aria-label="shapeTitle(article)"
        @click="emit('select', article.sectionId)"
      />
    </div>

    
  </div>
</template>
