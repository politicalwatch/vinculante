<script setup lang="ts">
withDefaults(defineProps<{
  text?: string
  title?: string
  /** Accessible name of the icon button. */
  label?: string
  side?: 'top' | 'bottom' | 'left' | 'right'
}>(), {
  text: undefined,
  title: undefined,
  label: 'Ayuda',
  side: 'bottom'
})
</script>

<template>
  <UPopover
    arrow
    :content="{ side, align: 'center', sideOffset: 6 }"
    :ui="{ content: 'max-w-72 p-3 text-xs leading-relaxed text-default' }"
  >
    <UButton
      icon="i-lucide-circle-help"
      color="neutral"
      variant="link"
      size="xs"
      class="p-0 text-dimmed hover:text-default"
      :aria-label="label"
    />

    <template #content>
      <p
        v-if="title"
        class="font-semibold text-highlighted mb-1"
      >
        {{ title }}
      </p>
      <slot>{{ text }}</slot>
    </template>
  </UPopover>
</template>
