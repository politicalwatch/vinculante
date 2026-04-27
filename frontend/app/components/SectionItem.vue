<script setup lang="ts">
import type { Section } from '~/types/api'

defineProps<{
  section: Section
  depth: number
  active: boolean
}>()

defineEmits<{ click: [] }>()
</script>

<template>
  <button
    class="w-full text-left px-4 py-3 border-b border-default transition-colors hover:bg-elevated"
    :class="active ? 'bg-primary/10 border-l-2 border-l-primary' : ''"
    :style="{ paddingLeft: `${16 + depth * 16}px` }"
    @click="$emit('click')"
  >
    <div v-if="section.section_number || section.section_type" class="text-xs text-muted mb-0.5 font-medium uppercase tracking-wide">
      {{ [section.section_number, section.section_type].filter(Boolean).join(' · ') }}
    </div>
    <p class="text-sm text-default whitespace-pre-line">
      {{ section.text }}
    </p>
  </button>
</template>
