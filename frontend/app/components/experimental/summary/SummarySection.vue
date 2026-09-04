<script setup lang="ts">
withDefaults(
  defineProps<{
    title: string
    anchor?: string
    underline?: boolean
    gap?: number
  }>(),
  { anchor: undefined, underline: true, gap: 24 }
)
</script>

<template>
  <section
    :id="anchor"
    class="flex flex-col scroll-mt-6"
    :style="{ gap: `${gap}px` }"
  >
    <h2
      class="section-heading"
      :class="underline ? 'is-underlined' : ''"
    >
      {{ title }}
    </h2>
    <slot />
  </section>
</template>

<style scoped>
.section-heading {
  align-self: flex-start;
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  color: var(--ed-accent);
}

.section-heading.is-underlined {
  padding-bottom: 12px;
  border-bottom: 2px solid var(--ed-accent);
}
</style>
