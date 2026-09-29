<script setup lang="ts">
import type { ResolvedHighlight } from '~/composables/useTargetSummary'

defineProps<{
  highlight: ResolvedHighlight
}>()
</script>

<template>
  <article
    class="flex flex-col gap-4 rounded-lg border border-ed-border border-l-4 border-l-ed-accent bg-ed-surface p-5"
    :title="highlight.relevance"
  >
    <p class="line-clamp-3 font-serif text-15 leading-normal text-ed-ink">
      &ldquo;{{ highlight.claim }}&rdquo;
    </p>
    <p class="text-xs font-bold tracking-wide text-ed-accent uppercase">
      {{ highlight.shortRef }}
    </p>
  </article>
</template>
