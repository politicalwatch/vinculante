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
      <svg
        class="h-9 w-auto"
        viewBox="0 86.7 512 338.8"
        fill="currentColor"
        aria-hidden="true"
      >
        <path d="M512,87.6l-111.9-1.2-19,30.6-75.6.9-128.6,268.2L45.8,116.3l52.1-.3,21.1,28.7h69.7l44.5,91.6,15.6-30.1-42.5-88.9h-73.6l-21.9-30.9-110.8.3,163.5,336.2c9,2.3,19.9,2.1,27.3-1l133.1-276.9,70.1.4,20.7-29.2,52.1-.3-130.9,269.2-56-113.8-15.4,32,44.9,93.7-89-.7-14.6,29.3,142.7-.5,163.6-337.4Z" />
        <path d="M512,87.6l-163.6,337.5-142.7.5,14.6-29.3,89,.7-44.9-93.7,15.4-32,56,113.8L466.7,115.9l-52.1.3-20.7,29.2-70.1-.4-133.1,276.9c-7.4,3.1-18.3,3.3-27.3,1L0,86.7l110.8-.3,21.9,31h73.6l42.5,88.8-15.6,30.1-44.5-91.8h-69.7l-21.1-28.6-52.1.3,131.1,269.8L305.5,117.9l75.6-.9,19.1-30.6,111.9,1.2Z" />
      </svg>
      <span class="font-serif text-22 font-bold italic">Vinculante</span>
    </NuxtLink>

    <template v-if="!isIndex">
      <nav
        class="mx-auto flex items-center gap-4"
        aria-label="Vista"
      >
        <NuxtLink
          :to="summaryPath"
          class="text-13 no-underline transition-colors"
          :class="!isDetail ? 'font-semibold text-ed-ink' : 'text-ed-muted hover:text-ed-ink'"
          :aria-current="!isDetail ? 'page' : undefined"
        >
          Resumen
        </NuxtLink>

        <span
          class="h-5 w-px bg-ed-border"
          aria-hidden="true"
        />

        <div class="flex items-center gap-1">
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
        </div>
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
