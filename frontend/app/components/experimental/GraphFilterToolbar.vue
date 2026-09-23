<script setup lang="ts">
import type {
  DegreeFloor,
  GraphFilters,
  LinkCountBounds,
  ProposalAuthorTypeFilter
} from '~/composables/useExperimentalGraph'

const props = withDefaults(defineProps<{
  filters: GraphFilters
  linkCountBounds: LinkCountBounds
  hasActiveFilters: boolean
  /** The article-count range only applies on the Propuestas tab. */
  showProposalArticleRange?: boolean
}>(), {
  showProposalArticleRange: true
})

const emit = defineEmits<{
  reset: []
}>()

const degreeFloorOptions: Array<{ label: string, value: DegreeFloor }> = [
  { label: 'Fuerte (alto)', value: 'alto' },
  { label: 'Moderado (medio)', value: 'medio' }
]

const authorTypeOptions: Array<{ label: string, value: ProposalAuthorTypeFilter }> = [
  { label: 'Todos', value: 'all' },
  { label: 'Ciudadanía', value: 'citizen' },
  { label: 'Grupo de expertos', value: 'academia' }
]

const articleMaxBound = computed(() => props.linkCountBounds.articleMax)
const proposalMaxBound = computed(() => props.linkCountBounds.proposalMax)

const articleLinksRange = computed({
  get: (): number[] => [
    props.filters.articleLinksMin,
    props.filters.articleLinksMax ?? articleMaxBound.value
  ],
  set: (value: number | number[] | undefined) => {
    const range = Array.isArray(value) ? value : [0, articleMaxBound.value]
    const min = Math.max(0, range[0] ?? 0)
    const max = Math.max(min, range[1] ?? articleMaxBound.value)
    props.filters.articleLinksMin = min
    props.filters.articleLinksMax = max >= articleMaxBound.value ? null : max
  }
})

const proposalLinksRange = computed({
  get: (): number[] => [
    props.filters.proposalLinksMin,
    props.filters.proposalLinksMax ?? proposalMaxBound.value
  ],
  set: (value: number | number[] | undefined) => {
    const range = Array.isArray(value) ? value : [0, proposalMaxBound.value]
    const min = Math.max(0, range[0] ?? 0)
    const max = Math.max(min, range[1] ?? proposalMaxBound.value)
    props.filters.proposalLinksMin = min
    props.filters.proposalLinksMax = max >= proposalMaxBound.value ? null : max
  }
})
</script>

<template>
  <div class="shrink-0 border-b border-default px-4 md:px-6 py-2 flex items-center gap-x-4 gap-y-2 flex-wrap">
    <div class="flex items-center gap-2">
      <span class="text-xs text-muted whitespace-nowrap">Grado mín.</span>
      <HelpTooltip
        label="Ayuda: Grado mínimo"
        text="Nivel mínimo de coincidencia entre una propuesta y un artículo para mostrar la vinculación. 'Fuerte' muestra solo las más claras; 'Moderado' añade también las de coincidencia media."
      />
      <USelect
        v-model="filters.degreeFloor"
        :items="degreeFloorOptions"
        size="xs"
        class="w-44"
      />
    </div>

    <div class="flex items-center gap-2 min-w-0">
      <span class="text-xs text-muted whitespace-nowrap">Artículos · vinculaciones</span>
      <HelpTooltip
        label="Ayuda: Artículos por número de vinculaciones"
        text="Muestra solo los artículos cuyo número de propuestas vinculadas está dentro de este rango. Útil para localizar artículos muy debatidos o sin apenas aportaciones."
      />
      <USlider
        v-model="articleLinksRange"
        :min="0"
        :max="Math.max(articleMaxBound, 1)"
        :step="1"
        size="xs"
        tooltip
        class="w-36"
      />
      <span class="text-xs text-muted tabular-nums whitespace-nowrap">
        {{ articleLinksRange[0] }}–{{ articleLinksRange[1] }}
      </span>
    </div>

    <div class="flex items-center gap-2">
      <span class="text-xs text-muted whitespace-nowrap">Propuestas · tipo</span>
      <HelpTooltip
        label="Ayuda: Tipo de propuesta"
        text="Filtra las propuestas según su origen: ciudadanía o grupo de expertos."
      />
      <USelect
        v-model="filters.proposalAuthorType"
        :items="authorTypeOptions"
        size="xs"
        class="w-40"
      />
    </div>

    <div
      v-if="showProposalArticleRange"
      class="flex items-center gap-2 min-w-0"
    >
      <span class="text-xs text-muted whitespace-nowrap">Propuestas · artículos</span>
      <HelpTooltip
        label="Ayuda: Propuestas por número de artículos"
        text="Muestra solo las propuestas vinculadas a un número de artículos dentro de este rango. Una propuesta con muchos artículos es transversal; con uno solo, es específica."
      />
      <USlider
        v-model="proposalLinksRange"
        :min="0"
        :max="Math.max(proposalMaxBound, 1)"
        :step="1"
        size="xs"
        tooltip
        class="w-36"
      />
      <span class="text-xs text-muted tabular-nums whitespace-nowrap">
        {{ proposalLinksRange[0] }}–{{ proposalLinksRange[1] }}
      </span>
    </div>

    <UButton
      v-if="hasActiveFilters"
      size="xs"
      color="neutral"
      variant="ghost"
      label="Restablecer filtros"
      class="ml-auto"
      @click="emit('reset')"
    />
  </div>
</template>
