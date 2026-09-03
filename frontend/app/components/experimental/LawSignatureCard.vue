<script setup lang="ts">
import type { VizTargetSignature } from '~/types/api'
import LawSignature from '~/components/experimental/LawSignature.vue'
import { topicOf } from '~/utils/topicPalette'

const SIGNATURE_SIZE = 264

const props = defineProps<{
  target: VizTargetSignature
  maxProposals: number
}>()

const topic = computed(() => topicOf(props.target.id))
const accent = computed(() => `var(${topic.value.cssVar})`)
</script>

<template>
  <NuxtLink
    :to="`/experimental/v3/${target.id}`"
    class="law-signature-card"
  >
    <header class="w-full">
      <div class="flex items-center justify-between gap-3">
        <span
          class="topic-tag"
          :style="{ '--topic-color': accent }"
        >
          {{ topic.label }}
        </span>
        <span
          class="author-badge"
          :style="{ '--topic-color': accent }"
        >
          {{ target.author }}
        </span>
      </div>
      <h2 class="mt-3 font-serif text-[20px] leading-snug font-semibold text-(--ed-ink) line-clamp-3">
        {{ target.title }}
      </h2>
    </header>

    <div class="signature-well">
      <LawSignature
        :articles="target.articles"
        :touched="target.touched"
        :proposals="target.proposals"
        :incorporated="target.incorporated"
        :max-proposals="maxProposals"
        :accent="accent"
        :size="SIGNATURE_SIZE"
      />
    </div>

    <footer class="w-full">
      <p class="text-[12px] text-(--ed-muted) tabular-nums leading-relaxed">
        {{ target.articles }} artículos · {{ target.touched }} con propuestas
        · {{ target.proposals }} propuestas · {{ target.incorporated }} incorporadas
      </p>
      <span class="cta">
        Ver vinculaciones
        <UIcon
          name="i-lucide-arrow-right"
          class="size-3.5"
        />
      </span>
    </footer>
  </NuxtLink>
</template>

<style scoped>
.law-signature-card {
  display: flex;
  flex-direction: column;
  gap: 24px;
  padding: 28px;
  background: var(--ed-surface);
  border: 1px solid var(--ed-border);
  border-radius: 8px;
  box-shadow: 0 4px 8px rgb(27 58 92 / 0.04);
  text-decoration: none;
  color: inherit;
  transition:
    border-color 0.2s ease,
    box-shadow 0.2s ease;
}

.law-signature-card:hover {
  border-color: var(--ed-ink);
  box-shadow:
    0 0 0 1px var(--ed-ink),
    0 8px 20px rgb(27 58 92 / 0.08);
}

.law-signature-card:hover .cta {
  gap: 8px;
}

.topic-tag {
  display: inline-flex;
  align-items: center;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--topic-color);
  white-space: nowrap;
}

.author-badge {
  display: inline-flex;
  align-items: center;
  height: 20px;
  padding: 0 8px;
  border-radius: 4px;
  background: color-mix(in oklab, var(--topic-color) 10%, transparent);
  color: var(--topic-color);
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  white-space: nowrap;
}

.signature-well {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  min-height: 300px;
  padding: 16px;
  background: var(--ed-surface-sunken);
  border-radius: 6px;
}

.cta {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  margin-top: 12px;
  font-size: 13px;
  font-weight: 600;
  color: var(--ed-accent);
  transition: gap 0.2s ease;
}
</style>
