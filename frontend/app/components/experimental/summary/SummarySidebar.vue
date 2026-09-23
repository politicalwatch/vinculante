<script setup lang="ts">
import type { CoverageStat, OrphanSection, ResolvedHighlight } from '~/composables/useTargetSummary'
import HighlightQuoteCard from '~/components/experimental/summary/HighlightQuoteCard.vue'
import SummarySection from '~/components/experimental/summary/SummarySection.vue'

const VISIBLE_HIGHLIGHTS = 2
const VISIBLE_ORPHANS = 4

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
</script>

<template>
  <aside class="flex flex-col gap-12 p-10">
    <div class="flex flex-col gap-6">
      <p class="font-serif text-sm leading-snug text-ed-ink/70">
        {{ title }}
      </p>

      <div
        v-if="coverage"
        class="flex items-center gap-8"
      >
        <div class="flex shrink-0 flex-col gap-1">
          <p class="font-serif text-56 font-extrabold text-ed-accent tabular-nums">
            {{ coverage.pct }}%
          </p>
          <p class="text-xs font-bold tracking-widest text-ed-ink/70 uppercase">
            Cobertura global
          </p>
        </div>

        <dl class="flex min-w-0 flex-1 flex-col gap-2">
          <div class="flex items-center justify-between gap-3 rounded-md border border-ed-border bg-ed-surface px-3 py-2 font-bold">
            <dt class="text-11 text-ed-ink/70 uppercase">
              Propuestas
            </dt>
            <dd class="text-13 text-ed-ink tabular-nums">
              {{ coverage.proposalsIncorporated }} / {{ coverage.proposalsTotal }}
            </dd>
          </div>
          <div class="flex items-center justify-between gap-3 rounded-md border border-ed-border bg-ed-degree-alto/10 px-3 py-2 font-bold">
            <dt class="text-11 text-ed-ink/70 uppercase">
              Fuerte
            </dt>
            <dd class="text-13 text-ed-degree-alto tabular-nums">
              {{ coverage.alto }}
            </dd>
          </div>
          <div class="flex items-center justify-between gap-3 rounded-md border border-ed-border bg-ed-degree-medio/10 px-3 py-2 font-bold">
            <dt class="text-11 text-ed-ink/70 uppercase">
              Moderado
            </dt>
            <dd class="text-13 text-ed-degree-medio tabular-nums">
              {{ coverage.medio }}
            </dd>
          </div>
        </dl>
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
