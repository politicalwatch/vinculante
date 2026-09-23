<script setup lang="ts">
import EditorialHeader from '~/components/experimental/editorial/EditorialHeader.vue'
</script>

<template>
  <div class="flex h-screen flex-col overflow-hidden bg-ed-bg text-ed-body">
    <EditorialHeader />

    <main class="flex-1 min-h-0 overflow-y-auto">
      <slot />
    </main>
  </div>
</template>
