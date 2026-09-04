<script setup lang="ts">
const route = useRoute()

const { data: laws, status: lawsStatus } = useLawIndex()

const targetId = computed(() => {
  const id = Number(route.params.id)
  return Number.isFinite(id) && id > 0 ? id : null
})

/** The catalogue page shows the brand alone: there is no session to describe. */
const isIndex = computed(() => targetId.value === null)

const sessionTitle = computed(
  () => laws.value?.find(law => law.id === targetId.value)?.title ?? ''
)

const summaryPath = computed(() => `/experimental/v3/${targetId.value}`)
const detailPath = computed(() => `${summaryPath.value}/detalle`)

const isDetail = computed(() => route.path === detailPath.value)
const isProposals = computed(() => isDetail.value && route.query.vista === 'propuestas')

const chips = computed(() => [
  {
    key: 'propuestas',
    label: 'Propuestas',
    to: { path: detailPath.value, query: { vista: 'propuestas' } },
    active: isProposals.value
  },
  {
    key: 'vinculaciones',
    label: 'Vinculaciones',
    to: { path: detailPath.value, query: { vista: 'vinculaciones' } },
    active: isDetail.value && !isProposals.value
  }
])

const lawItems = computed(() =>
  (laws.value ?? []).map(law => ({ label: law.title, id: law.id }))
)

function onSelectLaw(id: number) {
  navigateTo(`/experimental/v3/${id}`)
}
</script>

<template>
  <header class="editorial-top-bar shrink-0 flex items-center gap-6 px-6 xl:px-10 h-[68px]">
    <NuxtLink
      to="/experimental"
      class="brand"
      aria-label="Vinculante — todos los documentos"
    >
      <svg
        class="brand-mark"
        viewBox="0 86.7 512 338.8"
        fill="currentColor"
        aria-hidden="true"
      >
        <path d="M512,87.6l-111.9-1.2-19,30.6-75.6.9-128.6,268.2L45.8,116.3l52.1-.3,21.1,28.7h69.7l44.5,91.6,15.6-30.1-42.5-88.9h-73.6l-21.9-30.9-110.8.3,163.5,336.2c9,2.3,19.9,2.1,27.3-1l133.1-276.9,70.1.4,20.7-29.2,52.1-.3-130.9,269.2-56-113.8-15.4,32,44.9,93.7-89-.7-14.6,29.3,142.7-.5,163.6-337.4Z" />
        <path d="M512,87.6l-163.6,337.5-142.7.5,14.6-29.3,89,.7-44.9-93.7,15.4-32,56,113.8L466.7,115.9l-52.1.3-20.7,29.2-70.1-.4-133.1,276.9c-7.4,3.1-18.3,3.3-27.3,1L0,86.7l110.8-.3,21.9,31h73.6l42.5,88.8-15.6,30.1-44.5-91.8h-69.7l-21.1-28.6-52.1.3,131.1,269.8L305.5,117.9l75.6-.9,19.1-30.6,111.9,1.2Z" />
      </svg>
      <span class="brand-word">Vinculante</span>
    </NuxtLink>

    <template v-if="!isIndex">
      <nav
        class="flex items-center gap-4 mx-auto"
        aria-label="Vista"
      >
        <NuxtLink
          :to="summaryPath"
          class="nav-tab"
          :class="{ 'is-active': !isDetail }"
          :aria-current="!isDetail ? 'page' : undefined"
        >
          Resumen
        </NuxtLink>

        <span
          class="nav-divider"
          aria-hidden="true"
        />

        <div class="flex items-center gap-1">
          <NuxtLink
            v-for="chip in chips"
            :key="chip.key"
            :to="chip.to"
            class="layer-chip"
            :class="{ 'is-active': chip.active }"
            :aria-current="chip.active ? 'page' : undefined"
          >
            <span class="chip-dot" />
            {{ chip.label }}
          </NuxtLink>
        </div>
      </nav>

      <div class="flex items-center gap-4 min-w-0">
        <span class="hidden lg:block text-[13px] text-(--ed-muted) truncate max-w-[240px]">
          Sesión: {{ sessionTitle }}
        </span>

        <USelectMenu
          :items="lawItems"
          value-key="id"
          icon="i-lucide-search"
          color="neutral"
          variant="ghost"
          :loading="lawsStatus === 'pending'"
          :search-input="{ placeholder: 'Buscar una ley…' }"
          :ui="{
            base: 'size-8 shrink-0 rounded-full justify-center p-0 border border-(--ed-border) hover:bg-(--ed-surface-sunken)',
            leading: 'inset-0 justify-center',
            leadingIcon: 'size-4 text-(--ed-ink)',
            trailing: 'hidden',
            content: 'w-[420px]'
          }"
          aria-label="Buscar una ley"
          @update:model-value="onSelectLaw"
        />
      </div>
    </template>
  </header>
</template>

<style scoped>
.editorial-top-bar {
  background: var(--ed-surface);
  border-bottom: 1px solid var(--ed-border);
}

.brand {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-shrink: 0;
  color: var(--ed-ink);
  text-decoration: none;
}

.brand-mark {
  height: 37px;
  width: auto;
}

.brand-word {
  font-family: var(--font-serif, ui-serif, Georgia, serif);
  font-style: italic;
  font-size: 22px;
  font-weight: 700;
}

.nav-tab {
  font-size: 13px;
  color: var(--ed-muted);
  text-decoration: none;
  transition: color 0.2s ease;
}

.nav-tab:hover,
.nav-tab.is-active {
  color: var(--ed-ink);
}

.nav-tab.is-active {
  font-weight: 600;
}

.nav-divider {
  width: 1px;
  height: 20px;
  background: var(--ed-border);
}

.layer-chip {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  height: 32px;
  padding: 0 16px;
  border-radius: 16px;
  border: 1px solid transparent;
  color: var(--ed-muted);
  font-size: 13px;
  text-decoration: none;
  cursor: pointer;
  transition: background 0.2s ease, color 0.2s ease, border-color 0.2s ease;
}

.layer-chip:hover {
  color: var(--ed-ink);
}

.layer-chip .chip-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
  opacity: 0.5;
}

.layer-chip.is-active {
  background: var(--ed-ink);
  border-color: var(--ed-ink);
  color: var(--ed-surface);
}

.layer-chip.is-active .chip-dot {
  background: var(--ed-accent);
  opacity: 1;
}
</style>
