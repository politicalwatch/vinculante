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
  <aside class="summary-sidebar">
    <div class="flex flex-col gap-6">
      <p class="law-title">
        {{ title }}
      </p>

      <div
        v-if="coverage"
        class="flex items-center gap-8"
      >
        <div class="flex flex-col gap-1 shrink-0">
          <p class="coverage-value">
            {{ coverage.pct }}%
          </p>
          <p class="coverage-label">
            Cobertura global
          </p>
        </div>

        <dl class="flex-1 min-w-0 flex flex-col gap-2">
          <div class="kpi-row">
            <dt>Propuestas</dt>
            <dd>{{ coverage.proposalsIncorporated }} / {{ coverage.proposalsTotal }}</dd>
          </div>
          <div class="kpi-row is-alto">
            <dt>Fuerte</dt>
            <dd>{{ coverage.alto }}</dd>
          </div>
          <div class="kpi-row is-medio">
            <dt>Moderado</dt>
            <dd>{{ coverage.medio }}</dd>
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
        class="nav-link"
        :class="item.id === activeNavId ? 'is-active' : ''"
        :aria-current="item.id === activeNavId ? 'true' : undefined"
      >
        <span class="nav-dot" />
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
        class="see-all"
      >
        + Ver todas las vinculaciones
      </NuxtLink>
    </SummarySection>

    <SummarySection
      v-if="visibleOrphans.length"
      title="Propuestas no recogidas"
      :underline="false"
      :gap="20"
    >
      <ul class="flex flex-col gap-3">
        <li
          v-for="orphan in visibleOrphans"
          :key="orphan.sectionId"
          class="flex flex-col gap-1"
        >
          <p class="orphan-title">
            {{ orphan.title }}
          </p>
          <p class="orphan-note">
            {{ orphan.label }} · Brecha de cobertura detectada.
          </p>
        </li>
      </ul>
      <p
        v-if="remainingOrphans"
        class="orphan-note"
      >
        y {{ remainingOrphans }} artículos más sin vinculación aceptada.
      </p>
    </SummarySection>
  </aside>
</template>

<style scoped>
.summary-sidebar {
  display: flex;
  flex-direction: column;
  gap: 48px;
  padding: 40px;
}

.law-title {
  font-family: var(--font-serif, ui-serif, Georgia, serif);
  font-size: 14px;
  line-height: 1.45;
  color: var(--ed-ink);
  opacity: 0.7;
}

.coverage-value {
  font-family: var(--font-serif, ui-serif, Georgia, serif);
  font-size: 56px;
  font-weight: 800;
  line-height: 1;
  color: var(--ed-accent);
  font-variant-numeric: tabular-nums;
}

.coverage-label {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--ed-ink);
  opacity: 0.7;
}

.kpi-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 8px 12px;
  border: 1px solid var(--ed-border);
  border-radius: 6px;
  background: var(--ed-surface);
  font-weight: 700;
}

.kpi-row.is-alto {
  background: color-mix(in oklab, var(--ed-degree-alto) 10%, transparent);
}

.kpi-row.is-medio {
  background: color-mix(in oklab, var(--ed-degree-medio) 10%, transparent);
}

.kpi-row dt {
  font-size: 11px;
  text-transform: uppercase;
  color: var(--ed-ink);
  opacity: 0.7;
}

.kpi-row dd {
  font-size: 13px;
  color: var(--ed-ink);
  font-variant-numeric: tabular-nums;
}

.kpi-row.is-alto dd {
  color: var(--ed-degree-alto);
}

.kpi-row.is-medio dd {
  color: var(--ed-degree-medio);
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 14px;
  color: var(--ed-muted);
  text-decoration: none;
  transition: color 0.15s ease;
}

.nav-link .nav-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
  background: currentColor;
  opacity: 0.4;
  transition: opacity 0.15s ease, background 0.15s ease;
}

.nav-link:hover {
  color: var(--ed-ink);
}

.nav-link.is-active {
  color: var(--ed-ink);
  font-weight: 600;
}

.nav-link.is-active .nav-dot {
  background: var(--ed-accent);
  opacity: 1;
}

.see-all {
  font-size: 14px;
  font-weight: 700;
  color: var(--ed-accent);
  text-decoration: none;
}

.see-all:hover {
  text-decoration: underline;
}

.orphan-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--ed-ink);
}

.orphan-note {
  font-size: 12px;
  color: var(--ed-ink);
  opacity: 0.7;
}
</style>
