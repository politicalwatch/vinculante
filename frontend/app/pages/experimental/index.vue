<script setup lang="ts">
import type { VizTargetSignature } from '~/types/api'
import LawSignatureCard from '~/components/experimental/LawSignatureCard.vue'
import { TOPIC_PALETTE, topicCssVar } from '~/utils/topicPalette'

useSeoMeta({ title: 'Vinculante — Documentos objetivo' })

const api = useApi()
const { data: targets, status, error } = await useFetch<VizTargetSignature[]>('/viz_api/targets', { $fetch: api })

const maxProposals = computed(() =>
  Math.max(1, ...(targets.value ?? []).map(target => target.proposals))
)
</script>

<template>
  <div class="editorial-theme min-h-full">
    <UContainer class="py-12 max-w-(--breakpoint-2xl)">
      <div class="mb-8">
        <h1 class="font-serif text-5xl font-semibold text-(--ed-ink) mb-4 leading-[1.1]">
          Documentos objetivo
        </h1>
        <p class="text-(--ed-muted) max-w-2xl">
          Selecciona un documento para explorar las vinculaciones entre sus bloques y las propuestas ciudadanas.
        </p>
        <!-- <ul class="topic-legend mt-6">
          <li
            v-for="topic in TOPIC_PALETTE"
            :key="topic.key"
            class="topic-legend-item"
          >
            <span
              class="topic-legend-swatch"
              :style="{ background: `var(${topicCssVar(topic.key)})` }"
            />
            {{ topic.label }}
          </li>
        </ul> -->
      </div>

      <div
        v-if="status === 'pending'"
        class="grid grid-cols-1 md:grid-cols-2 gap-6"
      >
        <USkeleton
          v-for="n in 4"
          :key="n"
          class="h-128 rounded-lg"
        />
      </div>

      <UAlert
        v-else-if="error"
        color="error"
        icon="i-lucide-alert-circle"
        title="Error al cargar los documentos"
        :description="error.message"
      />

      <div
        v-else-if="targets?.length === 0"
        class="text-center py-16 text-(--ed-muted)"
      >
        No hay documentos disponibles.
      </div>

      <div
        v-else
        class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6"
      >
        <LawSignatureCard
          v-for="target in targets"
          :key="target.id"
          :target="target"
          :max-proposals="maxProposals"
        />
      </div>
    </UContainer>
  </div>
</template>

<style scoped>
.topic-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 16px;
}

.topic-legend-item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: var(--ed-muted);
}

.topic-legend-swatch {
  width: 10px;
  height: 10px;
  border-radius: 2px;
  flex-shrink: 0;
}
</style>
