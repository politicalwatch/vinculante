<script setup lang="ts">
import { select, type Selection } from 'd3-selection'
import { zoom, zoomIdentity, type ZoomBehavior } from 'd3-zoom'
import type { BallSimLink, BallSimNode } from '~/composables/useExperimentalBallGraph'
import {
  bezierPath,
  hexagonPoints
} from '~/composables/useExperimentalBallGraph'

const props = withDefaults(defineProps<{
  nodes: BallSimNode[]
  links: BallSimLink[]
  dimmedOpacity?: number
  draggable?: boolean
}>(), {
  draggable: true
})

const emit = defineEmits<{
  'node-click': [node: BallSimNode]
  'pane-click': []
  'drag-start': [nodeId: string]
  'drag': [nodeId: string, x: number, y: number]
  'drag-end': [nodeId: string]
}>()

const svgRef = ref<SVGSVGElement | null>(null)
const zoomLayerRef = ref<SVGGElement | null>(null)

const dimmedOpacity = computed(() => props.dimmedOpacity ?? 0.18)

let zoomBehavior: ZoomBehavior<SVGSVGElement, unknown> | null = null
let svgSelection: Selection<SVGSVGElement, unknown, null, undefined> | null = null
let transform = zoomIdentity

const dragState = ref<{
  nodeId: string
  pointerId: number
  moved: boolean
} | null>(null)

function screenToGraph(clientX: number, clientY: number): { x: number, y: number } {
  const svg = svgRef.value
  if (!svg) return { x: 0, y: 0 }
  const rect = svg.getBoundingClientRect()
  const sx = clientX - rect.left
  const sy = clientY - rect.top
  return {
    x: (sx - transform.x) / transform.k,
    y: (sy - transform.y) / transform.k
  }
}

function linkPath(link: BallSimLink, index: number): string {
  const source = link.source as BallSimNode
  const target = link.target as BallSimNode
  if (!source || !target || source.x == null || source.y == null || target.x == null || target.y == null) {
    return ''
  }
  return bezierPath(source.x, source.y, target.x, target.y, index)
}

function nodeOpacity(node: BallSimNode): number {
  if (node.dimmed) return dimmedOpacity.value
  return 1
}

function linkOpacity(link: BallSimLink): number {
  if (link.dimmed) return dimmedOpacity.value
  return link.animated ? 1 : 0.75
}

function onPointerDown(event: PointerEvent, node: BallSimNode) {
  if (event.button !== 0) return
  event.stopPropagation()
  ;(event.currentTarget as Element).setPointerCapture(event.pointerId)
  dragState.value = {
    nodeId: node.id,
    pointerId: event.pointerId,
    moved: false
  }
  if (props.draggable) {
    emit('drag-start', node.id)
  }
}

function onPointerMove(event: PointerEvent) {
  const state = dragState.value
  if (!state || event.pointerId !== state.pointerId) return
  if (!props.draggable) return
  state.moved = true
  const { x, y } = screenToGraph(event.clientX, event.clientY)
  emit('drag', state.nodeId, x, y)
}

function onPointerUp(event: PointerEvent, node: BallSimNode) {
  const state = dragState.value
  if (!state || event.pointerId !== state.pointerId) return
  ;(event.currentTarget as Element).releasePointerCapture(event.pointerId)
  if (props.draggable) {
    emit('drag-end', state.nodeId)
  }
  if (!state.moved) {
    emit('node-click', node)
  }
  dragState.value = null
}

function onBackgroundClick(event: MouseEvent) {
  if (event.target === svgRef.value || (event.target as Element)?.classList?.contains('ball-graph-bg')) {
    emit('pane-click')
  }
}

onMounted(() => {
  const svg = svgRef.value
  const layer = zoomLayerRef.value
  if (!svg || !layer) return

  svgSelection = select(svg)
  zoomBehavior = zoom<SVGSVGElement, unknown>()
    .scaleExtent([0.05, 4])
    .filter((event) => {
      // Allow wheel zoom always; pan only on background (not on nodes)
      if (event.type === 'wheel') return true
      const target = event.target as Element | null
      if (target?.closest?.('[data-ball-node]')) return false
      return !event.ctrlKey
    })
    .on('zoom', (event) => {
      transform = event.transform
      select(layer).attr('transform', event.transform.toString())
    })

  svgSelection.call(zoomBehavior)
})

onBeforeUnmount(() => {
  if (svgSelection && zoomBehavior) {
    svgSelection.on('.zoom', null)
  }
  zoomBehavior = null
  svgSelection = null
})
</script>

<template>
  <svg
    ref="svgRef"
    class="ball-graph-canvas w-full h-full touch-none"
    @click="onBackgroundClick"
  >
    <rect
      class="ball-graph-bg"
      width="100%"
      height="100%"
      fill="transparent"
    />
    <g ref="zoomLayerRef">
      <g class="links">
        <path
          v-for="(link, index) in links"
          :key="link.id"
          :d="linkPath(link, index)"
          fill="none"
          :stroke="link.stroke"
          :stroke-width="link.animated ? 2.5 : 1.25"
          :stroke-opacity="linkOpacity(link)"
          :class="{ 'ball-link-animated': link.animated }"
          stroke-linecap="round"
        />
      </g>

      <g class="nodes">
        <g
          v-for="node in nodes"
          :key="node.id"
          data-ball-node
          class="ball-node"
          :class="draggable ? 'cursor-grab active:cursor-grabbing' : 'cursor-pointer'"
          :opacity="nodeOpacity(node)"
          @pointerdown="onPointerDown($event, node)"
          @pointermove="onPointerMove"
          @pointerup="onPointerUp($event, node)"
          @pointercancel="onPointerUp($event, node)"
        >
          <circle
            v-if="node.kind === 'article'"
            :cx="node.x ?? 0"
            :cy="node.y ?? 0"
            :r="node.size"
            :fill="node.fill"
            :stroke="node.selected || node.highlighted ? '#2563eb' : 'transparent'"
            :stroke-width="node.selected ? 3 : node.highlighted ? 2 : 0"
          />
          <polygon
            v-else
            :points="hexagonPoints(node.x ?? 0, node.y ?? 0, node.size)"
            :fill="node.fill"
            :stroke="node.selected || node.highlighted ? '#b45309' : 'rgba(0,0,0,0.15)'"
            :stroke-width="node.selected ? 3 : node.highlighted ? 2 : 1"
          />
          <text
            v-if="node.kind === 'article'"
            :x="node.x ?? 0"
            :y="node.y ?? 0"
            text-anchor="middle"
            dominant-baseline="central"
            class="ball-label pointer-events-none"
            :font-size="Math.max(9, Math.min(14, node.size * 0.55))"
            fill="white"
            font-weight="600"
          >
            {{ node.label }}
          </text>
        </g>
      </g>
    </g>
  </svg>
</template>

<style scoped>
.ball-link-animated {
  stroke-dasharray: 8 6;
  animation: ball-link-dash 0.9s linear infinite;
}

@keyframes ball-link-dash {
  to {
    stroke-dashoffset: -28;
  }
}

.ball-label {
  user-select: none;
}
</style>
