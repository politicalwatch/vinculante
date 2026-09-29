<script setup lang="ts">
const props = withDefaults(
  defineProps<{
    title: string
    anchor?: string
    underline?: boolean
    /** Wider stack, used by the linkage chart. */
    loose?: boolean
  }>(),
  { anchor: undefined, underline: true, loose: false }
)
</script>

<template>
  <section
    :id="anchor"
    class="flex scroll-mt-6 flex-col"
    :class="props.loose ? 'gap-8' : 'gap-6'"
  >
    <h2
      class="self-start text-13 font-bold tracking-widest text-ed-accent uppercase"
      :class="underline ? 'border-b-2 border-ed-accent pb-3' : ''"
    >
      {{ title }}
    </h2>
    <slot />
  </section>
</template>
