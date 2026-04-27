<script setup lang="ts">
import type { Match } from '~/types/api'

const props = defineProps<{
  match: Match
  selected?: boolean
  hovered?: boolean
}>()

defineEmits<{
  hover: []
  leave: []
  click: []
}>()

const degreeColor = computed(() => props.match.degree === 'alto' ? 'primary' : 'neutral')
const degreeLabel = computed(() => props.match.degree === 'alto' ? 'Alto' : 'Medio')
const confidencePct = computed(() =>
  props.match.confidence !== null ? `${Math.round(props.match.confidence * 100)}%` : null
)

const authorTypeLabels: Record<string, string> = {
  citizens: 'Ciudadanía',
  academia: 'Academia'
}
const authorTypeLabel = computed(() => {
  const t = props.match.proposal.author_type
  if (!t) return null
  return authorTypeLabels[t] ?? t
})
</script>

<template>
  <UCard
    :ui="{ root: 'w-full shrink-0 cursor-pointer transition-all' }"
    :class="[
      selected ? 'ring-2 ring-primary' : '',
      hovered && !selected ? 'bg-primary/5' : ''
    ]"
    @mouseenter="$emit('hover')"
    @mouseleave="$emit('leave')"
    @click="$emit('click')"
  >
    <div class="flex flex-col gap-3">
      <!-- Header row: degree + author type + confidence -->
      <div class="flex items-center gap-2">
        <UBadge :color="degreeColor" variant="subtle" size="sm">
          {{ degreeLabel }}
        </UBadge>
        <UBadge v-if="authorTypeLabel" color="neutral" variant="outline" size="sm">
          {{ authorTypeLabel }}
        </UBadge>
        <span v-if="confidencePct" class="text-xs text-muted ml-auto">
          {{ confidencePct }} confianza
        </span>
      </div>

      <!-- Proposal text -->
      <p class="text-sm text-default">
        {{ match.proposal.text }}
      </p>

      <!-- Proposal metadata -->
      <div class="text-xs text-muted flex flex-wrap gap-x-3 gap-y-1">
        <span v-if="match.proposal.author">{{ match.proposal.author }}</span>
        <span v-if="match.proposal.reference">{{ match.proposal.reference }}</span>
        <span v-if="match.proposal.topic">{{ match.proposal.topic }}</span>
      </div>

      <!-- Explanation collapsible -->
      <UCollapsible v-if="match.explanation">
        <UButton
          variant="ghost"
          color="neutral"
          size="xs"
          trailing-icon="i-lucide-chevron-down"
          class="-mx-2"
        >
          Ver razonamiento
        </UButton>

        <template #content>
          <p class="text-xs text-muted mt-2 leading-relaxed whitespace-pre-line">
            {{ match.explanation }}
          </p>
        </template>
      </UCollapsible>
    </div>
  </UCard>
</template>
