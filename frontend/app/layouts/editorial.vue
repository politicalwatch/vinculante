<script setup lang="ts">
import EditorialHeader from '~/components/experimental/editorial/EditorialHeader.vue'
</script>

<template>
  <div class="editorial-theme flex flex-col h-screen overflow-hidden">
    <EditorialHeader />

    <main class="flex-1 min-h-0 overflow-y-auto">
      <slot />
    </main>
  </div>
</template>
