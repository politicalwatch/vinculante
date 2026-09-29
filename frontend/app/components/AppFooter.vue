<script setup lang="ts">
const config = useRuntimeConfig()
const { isModalActive } = useCookieControl()

// Same footer as the vinculante.ai landing (content/es/index.yml → footer)
const tagline = 'Vinculante.ai es un proyecto de Political Watch.'

const links = [
  { label: 'Political Watch', to: 'https://politicalwatch.es/' },
  { label: 'Aviso legal', to: 'https://politicalwatch.es/aviso-legal/' },
  { label: 'Privacidad', to: 'https://politicalwatch.es/politica-de-privacidad/' },
  { label: 'Cookies', to: 'https://politicalwatch.es/politica-de-cookies/' }
]
</script>

<template>
  <UFooter
    :ui="{
      container: 'border-t border-ed-border lg:py-8',
      right: 'gap-x-0 flex-wrap'
    }"
  >
    <template #left>
      <p class="text-sm text-dimmed">
        {{ tagline }} © {{ new Date().getFullYear() }}
      </p>
    </template>

    <template #right>
      <UButton
        v-for="link in links"
        :key="link.label"
        v-bind="link"
        color="neutral"
        variant="link"
        class="font-light"
        size="sm"
      />
      <!-- Lets visitors withdraw or give consent after the first choice. -->
      <UButton
        v-if="config.public.gtagId"
        label="Configurar cookies"
        color="neutral"
        variant="link"
        class="font-light"
        size="sm"
        @click="isModalActive = true"
      />
    </template>
  </UFooter>
</template>
