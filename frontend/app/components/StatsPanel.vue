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

type Bucket = { label: string; min: number; max: number | null }

const BUCKET_PRESETS: Bucket[][] = [
  // max ≤ 5
  [
    { label: '0', min: 0, max: 0 },
    { label: '1', min: 1, max: 1 },
    { label: '2', min: 2, max: 2 },
    { label: '3', min: 3, max: 3 },
    { label: '4-5', min: 4, max: 5 },
  ],
  // max ≤ 15
  [
    { label: '0', min: 0, max: 0 },
    { label: '1-2', min: 1, max: 2 },
    { label: '3-5', min: 3, max: 5 },
    { label: '6-10', min: 6, max: 10 },
    { label: '11-15', min: 11, max: 15 },
  ],
  // max ≤ 40
  [
    { label: '0', min: 0, max: 0 },
    { label: '1-5', min: 1, max: 5 },
    { label: '6-10', min: 6, max: 10 },
    { label: '11-20', min: 11, max: 20 },
    { label: '21-40', min: 21, max: 40 },
  ],
  // max > 40
  [
    { label: '0', min: 0, max: 0 },
    { label: '1-5', min: 1, max: 5 },
    { label: '6-15', min: 6, max: 15 },
    { label: '16-30', min: 16, max: 30 },
    { label: '31-50', min: 31, max: 50 },
    { label: '50+', min: 51, max: null },
  ],
]

function pickBuckets(maxVal: number): Bucket[] {
  if (maxVal <= 5) return BUCKET_PRESETS[0]
  if (maxVal <= 15) return BUCKET_PRESETS[1]
  if (maxVal <= 40) return BUCKET_PRESETS[2]
  return BUCKET_PRESETS[3]
}

const histogramData = computed(() => {
  const perSection = props.stats?.distribution.per_section ?? []
  const totals = perSection.map(s => s.alto + s.medio)
  const maxVal = totals.length ? Math.max(...totals) : 0
  const buckets = pickBuckets(maxVal)
  const counts = buckets.map(b =>
    totals.filter(v => v >= b.min && (b.max === null || v <= b.max)).length
  )
  return {
    labels: buckets.map(b => b.label),
    datasets: [
      {
        data: counts,
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
        label: 'Moderado',
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
            <span class="text-lg font-semibold text-highlighted tabular-nums">{{ stats.coverage.total_proposals }}</span>
            <span class="text-xs text-muted">propuestas totales</span>
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
              <span class="text-xs text-muted">Moderado</span>
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
            <span class="text-xs text-muted">moderado</span>
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
