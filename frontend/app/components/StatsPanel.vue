<script setup lang="ts">
import { Bar } from 'vue-chartjs'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Tooltip,
} from 'chart.js'
import type { TargetStats } from '~/types/api'

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip)

const props = defineProps<{
  stats: TargetStats | null
}>()

function pct(value: number) {
  return `${Math.round(value * 100)}%`
}

function conf(value: number | null) {
  return value !== null ? `${Math.round(value * 100)}%` : '—'
}

const altoPct = computed(() => {
  const total = (props.stats?.degree.alto.count ?? 0) + (props.stats?.degree.medio.count ?? 0)
  if (!total) return 0
  return Math.round(((props.stats?.degree.alto.count ?? 0) / total) * 100)
})

const medioPct = computed(() => 100 - altoPct.value)

const histogramData = computed(() => {
  const h = props.stats?.distribution.histogram
  return {
    labels: ['0', '1', '2', '3+'],
    datasets: [
      {
        data: h ? [h['0'], h['1'], h['2'], h['3+']] : [],
        backgroundColor: 'rgba(0, 0, 0, 0.65)',
        hoverBackgroundColor: 'rgba(0, 0, 0, 0.85)',
        borderRadius: 3,
        borderSkipped: false,
      },
    ],
  }
})

const histogramOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
    tooltip: {
      callbacks: {
        title: (items: any[]) => items[0].label === '1' ? '1 vinculación' : `${items[0].label} vinculaciones`,
        label: (item: any) => item.raw === 1 ? ' 1 sección' : ` ${item.raw} secciones`,
      },
    },
  },
  scales: {
    x: { grid: { display: false }, border: { display: false }, ticks: { font: { size: 11 } } },
    y: { display: false, beginAtZero: true },
  },
}

const perSectionData = computed(() => {
  const list = props.stats?.distribution.per_section ?? []
  return {
    labels: list.map((_, i) => String(i + 1)),
    datasets: [
      {
        label: 'Fuerte',
        data: list.map(s => s.alto),
        backgroundColor: 'rgba(34, 197, 94, 0.75)',
        stack: 'matches',
        borderWidth: 0,
      },
      {
        label: 'Débil',
        data: list.map(s => s.medio),
        backgroundColor: 'rgba(234, 179, 8, 0.75)',
        stack: 'matches',
        borderWidth: 0,
      },
    ],
  }
})

const perSectionOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: true, position: 'bottom' as const, labels: { font: { size: 11 }, boxWidth: 12 } },
    tooltip: {
      callbacks: {
        title: (items: any[]) => {
          const idx = items[0].dataIndex
          const sectionId = props.stats?.distribution.per_section[idx]?.section_id
          return `Sección #${idx + 1} (id ${sectionId})`
        },
      },
    },
  },
  scales: {
    x: {
      stacked: true,
      grid: { display: false },
      border: { display: false },
      ticks: { display: false },
    },
    y: {
      stacked: true,
      beginAtZero: true,
      grid: { color: 'rgba(0,0,0,0.06)' },
      border: { display: false },
      ticks: { font: { size: 11 }, precision: 0 },
    },
  },
}))

</script>

<template>
  <div v-if="stats" class="px-6 py-5">
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-x-8 gap-y-6">

      <!-- Coverage -->
      <div class="flex flex-col gap-3">
        <p class="text-xs font-medium text-muted uppercase tracking-wide">Cobertura</p>
        <div class="flex flex-col gap-2">
          <div class="flex items-baseline gap-2">
            <span class="text-2xl font-semibold text-highlighted tabular-nums">{{ pct(stats.coverage.pct_sections_matched) }}</span>
            <span class="text-xs text-muted">secciones vinculadas</span>
          </div>
          <div class="flex items-baseline gap-2">
            <span class="text-lg font-semibold text-highlighted tabular-nums">{{ stats.coverage.total_matches }}</span>
            <span class="text-xs text-muted">vinculaciones</span>
          </div>
          <div class="flex items-baseline gap-2">
            <span class="text-lg font-semibold text-highlighted tabular-nums">{{ stats.coverage.unique_proposals }}</span>
            <span class="text-xs text-muted">propuestas vinculadas</span>
          </div>
          <div class="flex items-baseline gap-2">
            <span class="text-lg font-semibold text-highlighted tabular-nums">{{ stats.coverage.total_proposals }}</span>
            <span class="text-xs text-muted">propuestas totales</span>
          </div>
        </div>
      </div>

      <!-- Degree distribution -->
      <div class="flex flex-col gap-3">
        <p class="text-xs font-medium text-muted uppercase tracking-wide">Grado</p>
        <div class="flex flex-col gap-2.5">
          <div>
            <div class="flex items-baseline justify-between mb-1">
              <span class="text-xs text-muted">Fuerte</span>
              <span class="text-xs tabular-nums text-default font-medium">{{ stats.degree.alto.count }}</span>
            </div>
            <div class="h-2 rounded-full bg-elevated overflow-hidden">
              <div class="h-full rounded-full bg-success" :style="{ width: `${altoPct}%` }" />
            </div>
          </div>
          <div>
            <div class="flex items-baseline justify-between mb-1">
              <span class="text-xs text-muted">Débil</span>
              <span class="text-xs tabular-nums text-default font-medium">{{ stats.degree.medio.count }}</span>
            </div>
            <div class="h-2 rounded-full bg-elevated overflow-hidden">
              <div class="h-full rounded-full bg-warning" :style="{ width: `${medioPct}%` }" />
            </div>
          </div>
        </div>
      </div>

      <!-- Confidence -->
      <div class="flex flex-col gap-3">
        <p class="text-xs font-medium text-muted uppercase tracking-wide">Confianza (media)</p>
        <div class="flex flex-col gap-2">
          <div class="flex items-baseline gap-2">
            <span class="text-2xl font-semibold text-highlighted tabular-nums">{{ conf(stats.confidence.mean) }}</span>
            <span class="text-xs text-muted">global</span>
          </div>
          <div class="flex items-baseline gap-2">
            <span class="text-lg font-semibold text-success tabular-nums">{{ conf(stats.confidence.by_degree.alto.mean) }}</span>
            <span class="text-xs text-muted">fuerte</span>
          </div>
          <div class="flex items-baseline gap-2">
            <span class="text-lg font-semibold text-warning tabular-nums">{{ conf(stats.confidence.by_degree.medio.mean) }}</span>
            <span class="text-xs text-muted">débil</span>
          </div>
        </div>
      </div>

      <!-- Histogram -->
      <div class="flex flex-col gap-3">
        <p class="text-xs font-medium text-muted uppercase tracking-wide">Vinculaciones / sección</p>
        <div class="h-32">
          <Bar :data="histogramData" :options="histogramOptions" />
        </div>
      </div>

    </div>

    <!-- Per-section distribution (full width, second row) -->
    <div v-if="(stats.distribution?.per_section?.length ?? 0) > 0" class="mt-6 pt-5 border-t border-default flex flex-col gap-3">
      <div>
        <p class="text-xs font-medium text-muted uppercase tracking-wide">Distribución por sección</p>
        <p class="text-xs text-muted mt-0.5">Número de vinculaciones a lo largo del documento</p>
      </div>
      <div class="h-48">
        <Bar :data="perSectionData" :options="perSectionOptions" />
      </div>
    </div>
  </div>
</template>
