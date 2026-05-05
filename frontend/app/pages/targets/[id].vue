<script setup lang="ts">
import type { TabsItem } from '@nuxt/ui'
import type { TargetDocument } from '~/types/api'

const route = useRoute()
const id = Number(route.params.id)
const api = useApi()

const { data: target, error: targetError } = await useFetch<TargetDocument>(
  `/targets/${id}`,
  { $fetch: api }
)

if (targetError.value) {
  throw createError({ statusCode: 404, message: 'Documento no encontrado' })
}

useSeoMeta({ title: () => `${target.value?.title ?? ''} — Vinculante` })

const view = ref<'overview' | 'analysis'>('overview')

const tabs: TabsItem[] = [
  { label: 'Resumen', value: 'overview', icon: 'i-lucide-file-text' },
  { label: 'Análisis', value: 'analysis', icon: 'i-lucide-list-tree' }
]
</script>

<template>
  <div class="h-full flex flex-col">
    <!-- Target header -->
    <div class="border-b border-default px-6 py-4 shrink-0">
      <NuxtLink
        to="/"
        class="text-sm text-muted hover:text-default flex items-center gap-1 mb-2"
      >
        <UIcon
          name="i-lucide-chevron-left"
          class="size-4"
        />
        Todos los documentos
      </NuxtLink>
      <div class="flex items-start justify-between gap-4">
        <div>
          <h1 class="text-2xl font-semibold text-highlighted">
            {{ target?.title }}
          </h1>
          <p class="text-sm text-muted mt-0.5">
            {{ target?.author }}
            <template v-if="target?.date">
              · {{ target.date }}
            </template>
            <template v-if="target?.version">
              · v{{ target.version }}
            </template>
          </p>
        </div>
        <UTabs
          v-model="view"
          :items="tabs"
          :content="false"
          color="neutral"
          variant="pill"
          size="sm"
        />
      </div>
    </div>

    <Transition
      enter-active-class="transition-opacity duration-150 ease-out"
      enter-from-class="opacity-0"
      leave-active-class="transition-opacity duration-100 ease-in"
      leave-to-class="opacity-0"
      mode="out-in"
    >
      <KeepAlive>
        <OverviewView
          v-if="view === 'overview'"
          key="overview"
          :target="target"
        />
        <AnalysisDetailsView
          v-else
          key="analysis"
          :target-id="id"
        />
      </KeepAlive>
    </Transition>
  </div>
</template>
