<script setup lang="ts">
import type { Section } from '~/types/api'
import ExpandableProse from '~/components/experimental/summary/ExpandableProse.vue'
import LinkageBarChart from '~/components/experimental/summary/LinkageBarChart.vue'
import SummarySection from '~/components/experimental/summary/SummarySection.vue'
import SummarySidebar from '~/components/experimental/summary/SummarySidebar.vue'
import { useTargetSummary } from '~/composables/useTargetSummary'
import { splitPullQuote } from '~/utils/summaryMarkdown'

definePageMeta({ layout: 'editorial', colorMode: 'light' })

const route = useRoute()
const id = Number(route.params.id)
const api = useApi()

const { data: target, error: targetError } = await useTargetDocument(id)

if (targetError.value) {
  throw createError({ statusCode: 404, message: 'Documento no encontrado' })
}

useSeoMeta({ title: () => `${target.value?.title ?? ''} — Vinculante` })

const { data: sections, status: sectionsStatus } = useFetch<Section[]>(
  '/sections',
  { $fetch: api, query: { target_id: id } }
)

const { blocks, hasSummary, coverage, groups, maxTotal, orphanSections, highlights }
  = useTargetSummary(target, sections)

const detailPath = computed(() => `/experimental/v3/${id}/detalle`)

const leyQuote = computed(() => splitPullQuote(blocks.value.ley?.paragraphs[0]))

/** The intro paragraph is consumed by the pull-quote split, so skip it here. */
const leyRemainder = computed(() => blocks.value.ley?.paragraphs.slice(1) ?? [])

const navItems = computed(() => {
  const items: Array<{ id: string, label: string }> = []
  if (blocks.value.ley) items.push({ id: 'resumen-ley', label: 'Resumen de la ley' })
  if (groups.value.length) items.push({ id: 'vinculaciones-detectadas', label: 'Vinculaciones detectadas' })
  if (blocks.value.linkages) items.push({ id: 'resumen-vinculaciones', label: 'Resumen de vinculaciones' })
  if (blocks.value.gaps) items.push({ id: 'propuestas-no-recogidas', label: 'Propuestas no recogidas' })
  return items
})

const activeNavId = ref('')

/** Distance from the top of the viewport at which a section becomes "current". */
const SPY_OFFSET = 160

/**
 * The page scrolls inside `UMain` rather than the document, so the spy listens
 * in the capture phase (scroll events do not bubble) and compares each anchor
 * against the viewport.
 */
function updateActiveNav() {
  const items = navItems.value
  let current = items[0]?.id ?? ''
  for (const item of items) {
    const el = document.getElementById(item.id)
    if (el && el.getBoundingClientRect().top <= SPY_OFFSET) current = item.id
  }
  activeNavId.value = current
}

onMounted(() => {
  document.addEventListener('scroll', updateActiveNav, { capture: true, passive: true })
  nextTick(updateActiveNav)
})

onBeforeUnmount(() => {
  document.removeEventListener('scroll', updateActiveNav, { capture: true })
})

watch(navItems, () => nextTick(updateActiveNav), { immediate: true })
</script>

<template>
  <div class="summary-page">
    <SummarySidebar
      class="summary-aside"
      :title="target?.title ?? ''"
      :coverage="coverage"
      :nav-items="navItems"
      :active-nav-id="activeNavId"
      :highlights="highlights"
      :orphan-sections="orphanSections"
      :detail-path="detailPath"
    />

    <div class="summary-main">
      <h1 class="law-heading">
        {{ target?.title }}
      </h1>

      <div
        v-if="!hasSummary"
        class="summary-notice"
      >
        <UIcon
          name="i-lucide-file-text"
          class="size-5 shrink-0 text-(--ed-accent)"
        />
        <div>
          <p class="font-semibold text-(--ed-ink)">
            Resumen no disponible
          </p>
          <p class="text-(--ed-body) mt-0.5">
            Este documento aún no tiene un resumen generado. Se muestran únicamente las
            vinculaciones detectadas.
          </p>
        </div>
      </div>

      <SummarySection
        v-if="blocks.ley"
        anchor="resumen-ley"
        title="Resumen de la ley"
      >
        <ExpandableProse
          :paragraphs="[leyQuote.before, leyQuote.after, ...leyRemainder].filter(Boolean)"
          :collapsed-count="1"
        >
          <template
            v-if="leyQuote.quote"
            #lead
          >
            <blockquote class="pull-quote">
              &ldquo;{{ leyQuote.quote }}&rdquo;
            </blockquote>
          </template>

          <template
            v-if="blocks.ley.bullets.length"
            #extra
          >
            <ul class="axis-list">
              <li
                v-for="(axis, index) in blocks.ley.bullets"
                :key="index"
              >
                {{ axis.text }}
              </li>
            </ul>
          </template>
        </ExpandableProse>
      </SummarySection>

      <SummarySection
        v-if="groups.length && coverage"
        anchor="vinculaciones-detectadas"
        title="Vinculaciones detectadas"
        :gap="32"
      >
        <LinkageBarChart
          :groups="groups"
          :max-total="maxTotal"
          :alto="coverage.alto"
          :medio="coverage.medio"
          :detail-path="detailPath"
        />
      </SummarySection>

      <SummarySection
        v-if="blocks.linkages"
        anchor="resumen-vinculaciones"
        title="Resumen de vinculaciones"
      >
        <ExpandableProse
          :paragraphs="blocks.linkages.paragraphs"
          :collapsed-count="1"
          :collapsed-lines="2"
        >
          <template
            v-if="blocks.linkages.bullets.length"
            #extra
          >
            <dl class="theme-list">
              <div
                v-for="(theme, index) in blocks.linkages.bullets"
                :key="index"
              >
                <dt>{{ theme.label }}</dt>
                <dd>{{ theme.text }}</dd>
              </div>
            </dl>
          </template>
        </ExpandableProse>
      </SummarySection>

      <SummarySection
        v-if="blocks.gaps"
        anchor="propuestas-no-recogidas"
        title="Propuestas no recogidas"
      >
        <ExpandableProse
          :paragraphs="blocks.gaps.paragraphs"
          :collapsed-count="1"
        />
      </SummarySection>

      <div
        v-if="sectionsStatus === 'pending'"
        class="flex justify-center py-8"
      >
        <UIcon
          name="i-lucide-loader-circle"
          class="size-6 animate-spin text-(--ed-muted)"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.summary-page {
  display: flex;
  align-items: flex-start;
  min-height: 100%;
}

.summary-aside {
  position: sticky;
  top: 0;
  flex-shrink: 0;
  width: 432px;
  max-height: calc(100vh - 68px);
  overflow-y: auto;
  overscroll-behavior: contain;
  border-right: 1px solid var(--ed-border);
}

.summary-main {
  display: flex;
  flex-direction: column;
  gap: 64px;
  flex: 1;
  min-width: 0;
  max-width: 920px;
  padding: 80px 60px;
}

.law-heading {
  font-family: var(--font-serif, ui-serif, Georgia, serif);
  font-size: 48px;
  font-weight: 800;
  line-height: 1.1;
  color: var(--ed-ink);
}

.summary-notice {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px 20px;
  border: 1px solid var(--ed-border);
  border-left: 4px solid var(--ed-accent);
  border-radius: 8px;
  background: var(--ed-surface);
  font-size: 14px;
}

.pull-quote {
  padding-left: 24px;
  border-left: 6px solid var(--ed-accent);
  font-family: var(--font-serif, ui-serif, Georgia, serif);
  font-size: 22px;
  line-height: 1.3;
  color: var(--ed-ink);
  max-width: 620px;
}

.axis-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding-left: 20px;
  list-style: disc;
  font-size: 15px;
  color: var(--ed-ink);
}

.theme-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.theme-list dt {
  font-size: 15px;
  font-weight: 600;
  color: var(--ed-ink);
  margin-bottom: 4px;
}

.theme-list dd {
  font-size: 15px;
  line-height: 1.6;
  color: var(--ed-ink);
  opacity: 0.85;
}

@media (max-width: 1023px) {
  .summary-page {
    flex-direction: column;
  }

  .summary-aside {
    position: static;
    width: 100%;
    max-height: none;
    border-right: none;
    border-bottom: 1px solid var(--ed-border);
  }

  .summary-main {
    padding: 40px 24px;
    gap: 48px;
  }

  .law-heading {
    font-size: 34px;
  }
}
</style>
