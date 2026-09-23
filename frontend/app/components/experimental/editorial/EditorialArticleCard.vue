<script setup lang="ts">
import type { EditorialArticle } from '~/composables/useEditorialBoard'

const props = defineProps<{
  article: EditorialArticle
  selected: boolean
  expanded: boolean
  opacity: number
}>()

const emit = defineEmits<{
  select: []
  toggleExpanded: []
}>()

const linkLabel = computed(() =>
  props.article.linkCount === 1
    ? '1 vinculación'
    : `${props.article.linkCount} vinculaciones`
)
</script>

<template>
  <article
    class="editorial-article-card"
    :class="props.selected ? 'is-selected' : ''"
    :style="{ opacity: props.opacity }"
  >
    <button
      type="button"
      class="w-full text-left px-[18px] pt-[18px] pb-3 cursor-pointer"
      :aria-pressed="props.selected"
      @click="emit('select')"
    >
      <div class="flex items-start justify-between gap-3">
        <span class="text-[10px] font-semibold tracking-[0.08em] text-(--ed-muted)">
          {{ props.article.label }}
        </span>
        <span
          v-if="props.article.linkCount > 0"
          class="mt-[3px] size-1.5 rounded-full shrink-0"
          :class="props.selected ? 'bg-(--ed-ink)' : 'bg-(--ed-accent)'"
        />
      </div>

      <h3 class="mt-2.5 font-serif text-[15px] leading-snug font-semibold text-(--ed-ink)">
        {{ props.article.title }}
      </h3>

      <p
        v-if="props.article.body"
        class="mt-2.5 text-[13px] leading-[1.55] text-(--ed-body) whitespace-pre-line"
        :class="props.expanded ? '' : 'line-clamp-3'"
      >
        {{ props.article.body }}
      </p>
    </button>

    <footer
      class="mt-auto flex items-center justify-between gap-2 border-t border-(--ed-border) px-[18px] py-2.5"
    >
      <span class="text-[11px] text-(--ed-muted) tabular-nums">
        {{ linkLabel }}
      </span>
      <button
        type="button"
        class="text-[11px] font-medium text-(--ed-accent) hover:underline cursor-pointer"
        :aria-expanded="props.expanded"
        @click.stop="emit('toggleExpanded')"
      >
        {{ props.expanded ? 'Leer menos' : 'Leer más' }}
      </button>
    </footer>
  </article>
</template>

<style scoped>
.editorial-article-card {
  display: flex;
  flex-direction: column;
  background: var(--ed-surface);
  border: 1px solid var(--ed-border);
  border-radius: 6px;
  box-shadow: 0 1px 2px rgb(27 58 92 / 0.05);
  transition:
    opacity 0.35s ease,
    border-color 0.25s ease,
    box-shadow 0.25s ease;
}

.editorial-article-card:hover:not(.is-selected) {
  border-color: rgb(27 58 92 / 0.22);
  box-shadow: 0 6px 16px rgb(27 58 92 / 0.1);
}

.editorial-article-card.is-selected {
  border-color: var(--ed-ink);
  box-shadow:
    0 0 0 1px var(--ed-ink),
    0 6px 16px rgb(27 58 92 / 0.1);
}
</style>
