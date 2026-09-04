<script setup lang="ts">
import type { LinkageGroup } from '~/composables/useTargetSummary'

const props = defineProps<{
  groups: LinkageGroup[]
  maxTotal: number
  alto: number
  medio: number
  detailPath: string
}>()

function widthPct(value: number): string {
  return `${(value / props.maxTotal) * 100}%`
}
</script>

<template>
  <div class="flex flex-col gap-8">
    <section
      v-for="group in groups"
      :key="group.key"
      class="flex flex-col gap-3"
    >
      <h3 class="group-label">
        {{ group.label }}
        <span
          v-if="group.subtitle"
          class="group-subtitle"
        >{{ group.subtitle }}</span>
      </h3>

      <ul class="flex flex-col gap-2">
        <li
          v-for="item in group.items"
          :key="item.sectionId"
        >
          <NuxtLink
            :to="detailPath"
            class="bar-row"
            :title="`${item.label}. ${item.title} — ${item.alto} fuertes, ${item.medio} moderados`"
          >
            <span class="bar-axis">{{ item.label }}</span>
            <span class="bar-track">
              <span
                v-if="item.alto"
                class="bar-fill"
                :style="{ width: widthPct(item.alto), background: 'var(--ed-degree-alto)' }"
              />
              <span
                v-if="item.medio"
                class="bar-fill"
                :style="{ width: widthPct(item.medio), background: 'var(--ed-degree-medio)' }"
              />
            </span>
            <span class="bar-total">{{ item.total }}</span>
          </NuxtLink>
        </li>
      </ul>
    </section>

    <div class="legend">
      <span class="legend-item">
        <span
          class="legend-swatch"
          :style="{ background: 'var(--ed-degree-alto)' }"
        />
        Vínculos fuertes ({{ alto }})
      </span>
      <span class="legend-item">
        <span
          class="legend-swatch"
          :style="{ background: 'var(--ed-degree-medio)' }"
        />
        Vínculos moderados ({{ medio }})
      </span>
    </div>
  </div>
</template>

<style scoped>
.group-label {
  display: flex;
  align-items: baseline;
  gap: 10px;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: color-mix(in oklab, var(--ed-ink) 70%, transparent);
}

.group-subtitle {
  font-size: 11px;
  font-weight: 400;
  letter-spacing: 0;
  text-transform: none;
  color: var(--ed-muted);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.bar-row {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 2px 4px;
  margin: 0 -4px;
  border-radius: 4px;
  color: inherit;
  text-decoration: none;
  transition: background 0.15s ease;
}

.bar-row:hover {
  background: color-mix(in oklab, var(--ed-accent) 6%, transparent);
}

.bar-axis {
  flex-shrink: 0;
  width: 60px;
  font-size: 13px;
  color: var(--ed-ink);
  font-variant-numeric: tabular-nums;
}

.bar-track {
  display: flex;
  flex: 1;
  min-width: 0;
  height: 16px;
  overflow: clip;
  border-radius: 2px;
  background: color-mix(in oklab, var(--ed-ink) 4%, transparent);
}

.bar-fill {
  height: 100%;
  flex-shrink: 0;
}

.bar-total {
  flex-shrink: 0;
  width: 40px;
  text-align: right;
  font-size: 12px;
  color: var(--ed-ink);
  opacity: 0.7;
  font-variant-numeric: tabular-nums;
}

.legend {
  display: flex;
  flex-wrap: wrap;
  gap: 24px;
  padding-top: 12px;
  border-top: 1px solid var(--ed-border);
}

.legend-item {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--ed-ink);
}

.legend-swatch {
  width: 12px;
  height: 12px;
  border-radius: 2px;
  flex-shrink: 0;
}
</style>
