<script setup lang="ts">
useHead({
  meta: [
    { name: 'viewport', content: 'width=device-width, initial-scale=1' }
  ],
  link: [
    { rel: 'icon', href: '/favicon.ico' }
  ],
  htmlAttrs: {
    lang: 'es'
  }
})

useSeoMeta({
  title: 'Vinculante',
  description: 'Analiza el grado de cobertura de propuestas ciudadanas en documentos normativos.'
})
</script>

<template>
  <UApp>
    <div class="flex flex-col h-screen overflow-hidden">
      <UHeader>
        <template #left>
          <NuxtLink to="/" aria-label="Vinculante" class="block">
            <img src="/logo.svg" alt="Vinculante" class="h-7 w-auto" />
          </NuxtLink>
        </template>

        <template #right>
          <UColorModeButton />
        </template>
      </UHeader>

      <UMain class="flex-1 min-h-0 overflow-y-auto">
        <NuxtPage />
      </UMain>

      <UFooter class="border-t border-default shrink-0">
        <template #left>
          <p class="text-sm text-muted">
            © {{ new Date().getFullYear() }} Political Watch
          </p>
        </template>
      </UFooter>
    </div>
  </UApp>
</template>
