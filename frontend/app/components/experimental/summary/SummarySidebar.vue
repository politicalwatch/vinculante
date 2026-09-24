<script setup lang="ts">
import type { CoverageStat, OrphanSection, ResolvedHighlight } from '~/composables/useTargetSummary'
import HighlightQuoteCard from '~/components/experimental/summary/HighlightQuoteCard.vue'
import SummarySection from '~/components/experimental/summary/SummarySection.vue'

const VISIBLE_HIGHLIGHTS = 2
const VISIBLE_ORPHANS = 4
const MIN_BAR_PCT = 40

const props = defineProps<{
  title: string
  coverage: CoverageStat | null
  navItems: Array<{ id: string, label: string }>
  activeNavId: string
  highlights: ResolvedHighlight[]
  orphanSections: OrphanSection[]
  detailPath: string
}>()

const visibleHighlights = computed(() => props.highlights.slice(0, VISIBLE_HIGHLIGHTS))
const visibleOrphans = computed(() => props.orphanSections.slice(0, VISIBLE_ORPHANS))
const remainingOrphans = computed(() => Math.max(0, props.orphanSections.length - VISIBLE_ORPHANS))

const statGroups = computed(() => {
  const c = props.coverage
  if (!c) return []
  return [
    {
      title: 'Propuestas',
      max: c.proposalsTotal,
      rows: [
        { label: 'Recibidas', value: c.proposalsTotal, class: 'bg-ed-surface text-ed-ink [&>dt]:opacity-70' },
        { label: 'Vinculadas', value: c.proposalsIncorporated, class: 'bg-ed-surface text-ed-accent [&>dt]:opacity-70' }
      ]
    },
    {
      title: 'Vinculaciones',
      max: Math.max(c.alto, c.medio),
      rows: [
        { label: 'Fuertes', value: c.alto, class: 'bg-ed-degree-alto text-white' },
        { label: 'Moderadas', value: c.medio, class: 'bg-ed-degree-medio text-white' }
      ]
    }
  ]
})

function barWidth(value: number, max: number) {
  const pct = max > 0 ? (value / max) * 100 : 100
  return `${Math.max(MIN_BAR_PCT, pct)}%`
}
</script>

<template>
  <aside class="flex flex-col gap-12 p-10">
    <div class="flex flex-col gap-6">
      <p class="font-serif text-sm leading-snug text-ed-ink/70">
        {{ title }}
      </p>

      <div
        v-if="coverage"
        class="flex flex-col gap-8"
      >
        <div class="flex items-center justify-between gap-6">
          <div class="flex flex-col gap-0.5 font-bold text-ed-ink/70">
            <p class="text-11 uppercase">
              Artículos con vinculaciones
            </p>
            <p class="text-base tabular-nums">
              {{ coverage.sectionsMatched }}/{{ coverage.sectionsTotal }}
            </p>
          </div>
          <p class="font-serif text-5xl font-black text-ed-accent tabular-nums">
            {{ coverage.pct }}%
          </p>
        </div>

        <div
          v-for="group in statGroups"
          :key="group.title"
          class="flex flex-col gap-2"
        >
          <p class="text-11 font-bold text-ed-ink/70 uppercase">
            {{ group.title }}
          </p>
          <dl class="flex flex-col gap-2">
            <div
              v-for="row in group.rows"
              :key="row.label"
              class="flex items-center justify-between gap-3 rounded-md border border-ed-border px-3 py-2 font-bold transition-[width] duration-500"
              :class="row.class"
              :style="{ width: barWidth(row.value, group.max) }"
            >
              <dt class="text-11 uppercase">
                {{ row.label }}
              </dt>
              <dd class="text-13 tabular-nums">
                {{ row.value }}
              </dd>
            </div>
          </dl>
        </div>
      </div>
    </div>

    <nav
      class="flex flex-col gap-3"
      aria-label="Secciones del resumen"
    >
      <a
        v-for="item in navItems"
        :key="item.id"
        :href="`#${item.id}`"
        class="flex items-center gap-3 text-sm text-ed-muted no-underline transition-colors hover:text-ed-ink"
        :class="item.id === activeNavId ? 'font-semibold text-ed-ink' : ''"
        :aria-current="item.id === activeNavId ? 'true' : undefined"
      >
        <span
          class="size-1.5 shrink-0 rounded-full"
          :class="item.id === activeNavId ? 'bg-ed-accent' : 'bg-current opacity-40'"
        />
        {{ item.label }}
      </a>
    </nav>

    <SummarySection
      v-if="visibleHighlights.length"
      title="Vinculaciones destacadas"
    >
      <div class="flex flex-col gap-6">
        <HighlightQuoteCard
          v-for="(highlight, index) in visibleHighlights"
          :key="index"
          :highlight="highlight"
        />
      </div>
      <NuxtLink
        :to="detailPath"
        class="text-sm font-bold text-ed-accent no-underline hover:underline"
      >
        + Ver todas las vinculaciones
      </NuxtLink>
    </SummarySection>

    <SummarySection
      v-if="visibleOrphans.length"
      title="Propuestas no recogidas"
      :underline="false"
    >
      <ul class="flex flex-col gap-3">
        <li
          v-for="orphan in visibleOrphans"
          :key="orphan.sectionId"
          class="flex flex-col gap-1"
        >
          <p class="text-sm font-semibold text-ed-ink">
            {{ orphan.title }}
          </p>
          <p class="text-xs text-ed-ink/70">
            {{ orphan.label }} · Brecha de cobertura detectada.
          </p>
        </li>
      </ul>
      <p
        v-if="remainingOrphans"
        class="text-xs text-ed-ink/70"
      >
        y {{ remainingOrphans }} artículos más sin vinculación aceptada.
      </p>
    </SummarySection>
  </aside>
</template>
