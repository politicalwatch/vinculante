<script setup lang="ts">
const route = useRoute()

const { data: laws, status: lawsStatus } = useLawIndex()

const targetId = computed(() => {
  const id = Number(route.params.id)
  return Number.isFinite(id) && id > 0 ? id : null
})

/** The catalogue page shows the brand alone: there is no session to describe. */
const isIndex = computed(() => targetId.value === null)

const summaryPath = computed(() => `/experimental/v3/${targetId.value}`)
const detailPath = computed(() => `${summaryPath.value}/detalle`)

const isDetail = computed(() => route.path === detailPath.value)
const isProposals = computed(() => isDetail.value && route.query.vista === 'propuestas')

const chips = computed(() => [
  {
    key: 'resumen',
    label: 'Resumen',
    to: summaryPath.value,
    active: !isDetail.value
  },
  {
    key: 'vinculaciones',
    label: 'Vinculaciones',
    to: { path: detailPath.value, query: { vista: 'vinculaciones' } },
    active: isDetail.value && !isProposals.value
  },
  {
    key: 'propuestas',
    label: 'Propuestas',
    to: { path: detailPath.value, query: { vista: 'propuestas' } },
    active: isProposals.value
  }
])

const lawItems = computed(() =>
  (laws.value ?? []).map(law => ({ label: law.title, value: law.id }))
)

function onSelectLaw(id: number) {
  if (!Number.isFinite(id) || id === targetId.value) return
  navigateTo(`/experimental/v3/${id}`)
}
</script>

<template>
  <header class="flex h-17 shrink-0 items-center gap-6 border-b border-ed-border bg-ed-surface px-6 xl:px-10">
    <NuxtLink
      to="/experimental"
      class="flex shrink-0 items-center gap-4 text-ed-ink no-underline"
      aria-label="Vinculante — todos los documentos"
    >
      <span class="font-serif text-[1.375rem]/[1.3] font-bold italic text-ed-ink">Vinculante<span class="font-mono text-ed-accent">.ai</span></span>
    </NuxtLink>

    <template v-if="!isIndex">
      <nav
        class="mx-auto flex items-center gap-1"
        aria-label="Vista"
      >
        <NuxtLink
          v-for="chip in chips"
          :key="chip.key"
          :to="chip.to"
          class="inline-flex h-8 items-center gap-2 rounded-full border border-transparent px-4 text-13 no-underline transition-colors"
          :class="chip.active
            ? 'border-ed-ink bg-ed-ink text-ed-surface'
            : 'text-ed-muted hover:text-ed-ink'"
          :aria-current="chip.active ? 'page' : undefined"
        >
          <span
            class="size-1.5 rounded-full"
            :class="chip.active ? 'bg-ed-accent' : 'bg-current opacity-50'"
          />
          {{ chip.label }}
        </NuxtLink>
      </nav>

      <USelect
        :model-value="targetId ?? undefined"
        :items="lawItems"
        color="neutral"
        variant="ghost"
        size="sm"
        :loading="lawsStatus === 'pending'"
        placeholder="Selecciona una ley"
        class="w-64 min-w-0 lg:w-80"
        aria-label="Seleccionar una ley"
        @update:model-value="onSelectLaw"
      />
    </template>
  </header>
</template>
