<script setup lang="ts">
interface Layers {
  articles: boolean
  proposals: boolean
  links: boolean
}

const props = defineProps<{
  layers: Layers
  sessionTitle: string
}>()

const emit = defineEmits<{
  toggleLayer: [key: keyof Layers]
}>()

const chips: Array<{ key: keyof Layers, label: string }> = [
  { key: 'articles', label: 'Artículos' },
  { key: 'proposals', label: 'Propuestas' },
  { key: 'links', label: 'Vinculaciones' }
]
</script>

<template>
  <header class="editorial-top-bar shrink-0 flex items-center gap-6 px-6 xl:px-10 h-[68px]">
    <div class="flex items-center gap-4 shrink-0">
      <span class="font-serif italic text-[22px] font-bold text-(--ed-ink)">
        Vinculante
      </span>
      <span class="analysis-badge">
        <span class="size-1.5 rounded-full bg-(--ed-accent)" />
        ANÁLISIS ACTIVO
      </span>
    </div>

    <nav
      class="flex items-center gap-2.5 mx-auto"
      aria-label="Capas visibles"
    >
      <button
        v-for="chip in chips"
        :key="chip.key"
        type="button"
        class="layer-chip"
        :class="props.layers[chip.key] ? 'is-active' : ''"
        :aria-pressed="props.layers[chip.key]"
        @click="emit('toggleLayer', chip.key)"
      >
        <span class="chip-dot" />
        {{ chip.label }}
      </button>
    </nav>

    <div class="flex items-center gap-4 min-w-0">
      <span class="hidden lg:block text-[13px] text-(--ed-muted) truncate max-w-[240px]">
        Sesión: {{ props.sessionTitle }}
      </span>
      <UButton
        icon="i-lucide-settings"
        color="neutral"
        variant="ghost"
        size="sm"
        aria-label="Ajustes"
      />
    </div>
  </header>
</template>

<style scoped>
.editorial-top-bar {
  background: var(--ed-surface);
  border-bottom: 1px solid var(--ed-border);
}

.analysis-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 22px;
  padding: 0 10px;
  border-radius: 11px;
  background: color-mix(in oklab, var(--ed-accent) 12%, transparent);
  color: var(--ed-accent);
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.06em;
}

.layer-chip {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  height: 32px;
  padding: 0 16px;
  border-radius: 16px;
  border: 1px solid var(--ed-border);
  background: var(--ed-surface);
  color: var(--ed-muted);
  font-size: 13px;
  cursor: pointer;
  transition: background 0.2s ease, color 0.2s ease, border-color 0.2s ease;
}

.layer-chip .chip-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
  opacity: 0.5;
}

.layer-chip.is-active {
  background: var(--ed-ink);
  border-color: var(--ed-ink);
  color: var(--ed-surface);
}

.layer-chip.is-active .chip-dot {
  background: var(--ed-accent);
  opacity: 1;
}
</style>
