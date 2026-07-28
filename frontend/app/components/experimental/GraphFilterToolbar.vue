<script setup lang="ts">
import type {
  DegreeFloor,
  GraphFilters,
  LinkCountBounds,
  ProposalAuthorTypeFilter
} from '~/composables/useExperimentalGraph'

const props = defineProps<{
  filters: GraphFilters
  linkCountBounds: LinkCountBounds
  hasActiveFilters: boolean
}>()

const emit = defineEmits<{
  reset: []
}>()

const degreeFloorOptions: Array<{ label: string, value: DegreeFloor }> = [
  { label: 'Fuerte (alto)', value: 'alto' },
  { label: 'Moderado (medio)', value: 'medio' },
  { label: 'Débil (bajo)', value: 'bajo' }
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
      <USelect
        v-model="filters.degreeFloor"
        :items="degreeFloorOptions"
        size="xs"
        class="w-44"
      />
    </div>

    <div class="flex items-center gap-2 min-w-0">
      <span class="text-xs text-muted whitespace-nowrap">Artículos · vinculaciones</span>
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
      <USelect
        v-model="filters.proposalAuthorType"
        :items="authorTypeOptions"
        size="xs"
        class="w-40"
      />
    </div>

    <div class="flex items-center gap-2 min-w-0">
      <span class="text-xs text-muted whitespace-nowrap">Propuestas · artículos</span>
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
