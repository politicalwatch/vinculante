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

// Same title, description and social card as the vinculante.ai landing
const title = 'Vinculante.ai — La participación que deja huella'
const description = 'Vinculante.ai analiza las aportaciones de un proceso participativo para identificar de manera automática de qué forma han quedado recogidas, con qué grado y explicando el por qué. Trazabilidad verificable entre lo que se propuso y el texto que finalmente vio la luz.'

useSeoMeta({
  title,
  // Page titles already name the site, so skip Nuxt SEO's "%s | Vinculante.ai" template
  titleTemplate: '%s',
  ogTitle: title,
  description,
  ogDescription: description,
  ogLocale: 'es_ES',
  // Static screenshot of the vinculante.ai hero, copied from that repo's public/og-image.png
  ogImage: {
    url: '/og-image.png',
    width: 1200,
    height: 630,
    type: 'image/png',
    alt: title
  },
  twitterCard: 'summary_large_image',
  twitterImageAlt: title
})
</script>

<template>
  <UApp>
    <NuxtLoadingIndicator color="var(--ui-primary)" />
    <NuxtLayout>
      <NuxtPage />
    </NuxtLayout>
  </UApp>
</template>
