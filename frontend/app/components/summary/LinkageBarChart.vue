<script setup lang="ts">
import type { LinkageGroup } from '~/composables/useTargetSummary'

const props = defineProps<{
  groups: LinkageGroup[]
  maxTotal: number
  alto: number
  medio: number
  detailPath: string
}>()

function widthPct(value: number): string {
  return `${(value / props.maxTotal) * 100}%`
}
</script>

<template>
  <div class="flex flex-col gap-8">
    <section
      v-for="group in groups"
      :key="group.key"
      class="flex flex-col gap-3"
    >
      <h3 class="flex items-baseline gap-2.5 text-xs font-bold tracking-widest text-ed-ink/70 uppercase">
        {{ group.label }}
        <span
          v-if="group.subtitle"
          class="truncate text-11 font-normal tracking-normal text-ed-muted normal-case"
        >{{ group.subtitle }}</span>
      </h3>

      <ul class="flex flex-col gap-2">
        <li
          v-for="item in group.items"
          :key="item.sectionId"
        >
          <NuxtLink
            :to="detailPath"
            class="-mx-1 flex items-center gap-4 rounded px-1 py-0.5 text-inherit no-underline transition-colors hover:bg-ed-accent/5"
            :title="`${item.label}. ${item.title} — ${item.alto} fuertes, ${item.medio} moderados`"
          >
            <span class="w-15 shrink-0 text-13 text-ed-ink tabular-nums">{{ item.label }}</span>
            <span class="flex h-4 min-w-0 flex-1 overflow-clip rounded-sm bg-ed-ink/5">
              <span
                v-if="item.alto"
                class="h-full shrink-0 bg-ed-degree-alto"
                :style="{ width: widthPct(item.alto) }"
              />
              <span
                v-if="item.medio"
                class="h-full shrink-0 bg-ed-degree-medio"
                :style="{ width: widthPct(item.medio) }"
              />
            </span>
            <span class="w-10 shrink-0 text-right text-xs text-ed-ink/70 tabular-nums">{{ item.total }}</span>
          </NuxtLink>
        </li>
      </ul>
    </section>

    <div class="flex flex-wrap gap-6 border-t border-ed-border pt-3">
      <span class="inline-flex items-center gap-2 text-xs text-ed-ink">
        <span class="size-3 shrink-0 rounded-sm bg-ed-degree-alto" />
        Vínculos fuertes ({{ alto }})
      </span>
      <span class="inline-flex items-center gap-2 text-xs text-ed-ink">
        <span class="size-3 shrink-0 rounded-sm bg-ed-degree-medio" />
        Vínculos moderados ({{ medio }})
      </span>
    </div>
  </div>
</template>
