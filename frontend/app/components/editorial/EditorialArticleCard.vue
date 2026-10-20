<script setup lang="ts">
import type { EditorialArticle } from '~/composables/useEditorialBoard'

const props = defineProps<{
  article: EditorialArticle
  selected: boolean
  expanded: boolean
  opacity: number
  /** Below `sm`, render as an edge-to-edge row instead of a floating card. */
  flush?: boolean
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
    class="flex flex-col border-ed-border bg-ed-surface transition-shadow"
    :class="[
      props.flush
        ? 'border-b sm:rounded-md sm:border sm:shadow-sm mb-4 sm:mb-0'
        : 'rounded-md border shadow-sm',
      props.selected
        ? ['border-ed-ink ring-1 ring-ed-ink', props.flush ? 'max-sm:ring-inset' : '']
        : 'hover:border-ed-ink/20 hover:shadow-md'
    ]"
    :style="{ opacity: props.opacity }"
  >
    <button
      type="button"
      class="w-full cursor-pointer px-4 pt-4 pb-3 text-left"
      :aria-pressed="props.selected"
      @click="emit('select')"
    >
      <div class="flex items-start justify-between gap-3">
        <span class="text-2xs font-semibold tracking-widest text-ed-muted">
          {{ props.article.label }}
        </span>
        <span
          v-if="props.article.linkCount > 0"
          class="mt-0.5 size-1.5 shrink-0 rounded-full"
          :class="props.selected ? 'bg-ed-ink' : 'bg-ed-accent'"
        />
      </div>

      <h3 class="mt-2.5 font-serif text-15 leading-snug font-semibold text-ed-ink">
        {{ props.article.title }}
      </h3>

      <p
        v-if="props.article.body"
        class="mt-2.5 text-13 text-ed-body whitespace-pre-line"
        :class="props.expanded ? '' : 'line-clamp-3'"
      >
        {{ props.article.body }}
      </p>
    </button>

    <footer class="mt-auto flex items-center justify-between gap-2 border-t border-ed-border px-4 py-2.5">
      <span class="text-11 text-ed-muted tabular-nums">
        {{ linkLabel }}
      </span>
      <button
        type="button"
        class="cursor-pointer text-11 font-medium text-ed-accent hover:underline"
        :aria-expanded="props.expanded"
        @click.stop="emit('toggleExpanded')"
      >
        {{ props.expanded ? 'Leer menos' : 'Leer más' }}
      </button>
    </footer>
  </article>
</template>
