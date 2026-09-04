<template>
  <div class="flex flex-col h-screen overflow-hidden">
    <UHeader>
      <template #left>
        <NuxtLink to="/" aria-label="Vinculante" class="block">
          <img src="/logo.svg" alt="Vinculante" class="h-7 w-auto block dark:hidden" />
          <img src="/logo-white.svg" alt="Vinculante" aria-hidden="true" class="h-7 w-auto hidden dark:block" />
        </NuxtLink>
      </template>

      <template #right>
        <UColorModeButton />
      </template>
    </UHeader>

    <UMain class="flex-1 min-h-0 overflow-y-auto">
      <slot />
    </UMain>

    <UFooter class="border-t border-default shrink-0" :ui="{ container: 'py-2 sm:py-4 lg:flex lg:items-center lg:justify-between lg:gap-x-3' }">
      <template #left>
        <p class="text-sm text-muted">
          Una iniciativa de <a href="https://www.politicalwatch.es" target="_blank" rel="noopener noreferrer" class="text-primary hover:underline">Political Watch</a>
        </p>
      </template>
    </UFooter>
  </div>
</template>
