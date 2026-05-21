<script setup lang="ts">
import type { TargetDocument } from '~/types/api'

useSeoMeta({ title: 'Vinculante — Documentos objetivo' })

const api = useApi()
const { data: targets, status, error } = await useFetch<TargetDocument[]>('/targets', { $fetch: api })
</script>

<template>
  <UContainer class="py-12">
    <div class="mb-8">
      <h1 class="text-3xl font-bold text-highlighted mb-2">
        Documentos objetivo
      </h1>
      <p class="text-muted">
        Selecciona un documento para explorar las vinculaciones entre sus bloques y las propuestas ciudadanas.
      </p>
    </div>

    <div v-if="status === 'pending'" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <USkeleton v-for="n in 6" :key="n" class="h-40 rounded-lg" />
    </div>

    <UAlert
      v-else-if="error"
      color="error"
      icon="i-lucide-alert-circle"
      title="Error al cargar los documentos"
      :description="error.message"
    />

    <div v-else-if="targets?.length === 0" class="text-center py-16 text-muted">
      No hay documentos disponibles.
    </div>

    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <TargetCard v-for="target in targets" :key="target.id" :target="target" />
    </div>
  </UContainer>
</template>
