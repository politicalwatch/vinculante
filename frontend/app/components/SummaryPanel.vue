<script setup lang="ts">
defineProps<{
  summary: string | null
}>()
</script>

<template>
  <div class="h-full overflow-y-auto px-6 py-5">
    <div v-if="summary" class="prose prose-sm max-w-none dark:prose-invert">
      <MDC :value="summary" />
    </div>
    <div v-else class="flex flex-col items-center justify-center h-full gap-3 px-8 text-center">
      <UIcon
        name="i-lucide-file-text"
        class="size-10 text-muted"
      />
      <p class="text-muted text-sm">
        Resumen no disponible aún.
      </p>
    </div>
  </div>
</template>
