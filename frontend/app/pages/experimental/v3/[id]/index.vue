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
  if (blocks.value.linkages) items.push({ id: 'resumen-vinculaciones', label: 'Resumen de vinculaciones' })
  if (groups.value.length) items.push({ id: 'vinculaciones-detectadas', label: 'Vinculaciones detectadas' })
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
  <div class="flex min-h-full flex-col items-start lg:flex-row">
    <SummarySidebar
      class="w-full shrink-0 overflow-y-auto overscroll-contain border-b border-ed-border lg:sticky lg:top-0 lg:w-md lg:max-h-[calc(100vh-4.25rem)] lg:border-r lg:border-b-0"
      :title="target?.title ?? ''"
      :coverage="coverage"
      :nav-items="navItems"
      :active-nav-id="activeNavId"
      :highlights="highlights"
      :orphan-sections="orphanSections"
      :detail-path="detailPath"
    />

    <div class="flex w-full min-w-0 max-w-4xl flex-1 flex-col gap-12 px-6 py-10 lg:gap-16 lg:px-14 lg:py-20">
      <h1 class="font-serif text-34 font-extrabold text-ed-ink lg:text-5xl">
        {{ target?.title }}
      </h1>

      <div
        v-if="!hasSummary"
        class="flex items-start gap-3 rounded-lg border border-ed-border border-l-4 border-l-ed-accent bg-ed-surface px-5 py-4 text-sm"
      >
        <UIcon
          name="i-lucide-file-text"
          class="size-5 shrink-0 text-ed-accent"
        />
        <div>
          <p class="font-semibold text-ed-ink">
            Resumen no disponible
          </p>
          <p class="mt-0.5 text-ed-body">
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
            <blockquote class="max-w-xl border-l-8 border-ed-accent pl-6 font-serif text-22 text-ed-ink">
              &ldquo;{{ leyQuote.quote }}&rdquo;
            </blockquote>
          </template>

          <template
            v-if="blocks.ley.bullets.length"
            #extra
          >
            <ul class="flex list-disc flex-col gap-2 pl-5 text-15 text-ed-ink">
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
            <dl class="flex flex-col gap-4">
              <div
                v-for="(theme, index) in blocks.linkages.bullets"
                :key="index"
              >
                <dt class="mb-1 text-15 font-semibold text-ed-ink">
                  {{ theme.label }}
                </dt>
                <dd class="text-15 leading-relaxed text-ed-ink/85">
                  {{ theme.text }}
                </dd>
              </div>
            </dl>
          </template>
        </ExpandableProse>
      </SummarySection>

      <SummarySection
        v-if="groups.length && coverage"
        anchor="vinculaciones-detectadas"
        title="Vinculaciones detectadas"
        loose
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
          class="size-6 animate-spin text-ed-muted"
        />
      </div>
    </div>
  </div>
</template>
