<script setup lang="ts">
import type { ResolvedHighlight } from '~/composables/useTargetSummary'

defineProps<{
  highlight: ResolvedHighlight
}>()
</script>

<template>
  <article
    class="highlight-card"
    :title="highlight.relevance"
  >
    <p class="highlight-quote">
      &ldquo;{{ highlight.claim }}&rdquo;
    </p>
    <p class="highlight-ref">
      {{ highlight.shortRef }}
    </p>
  </article>
</template>

<style scoped>
.highlight-card {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 20px;
  background: var(--ed-surface);
  border: 1px solid var(--ed-border);
  border-left: 4px solid var(--ed-accent);
  border-radius: 8px;
}

.highlight-quote {
  font-family: var(--font-serif, ui-serif, Georgia, serif);
  font-size: 15px;
  line-height: 1.45;
  color: var(--ed-ink);
  display: -webkit-box;
  -webkit-line-clamp: 3;
  line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.highlight-ref {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--ed-accent);
}
</style>
