import {
  forceCollide,
  forceLink,
  forceManyBody,
  forceSimulation,
  forceX,
  forceY,
  type SimulationLinkDatum,
  type SimulationNodeDatum
} from 'd3-force'
import { interpolateInferno } from 'd3-scale-chromatic'
import type { Edge, Node } from '@vue-flow/core'
import type { Match, MatchDegree, Proposal, Section } from '~/types/api'

const NODE_WIDTH = 340
const NODE_HEIGHT = 150
const COLUMN_INSET = 48
const ARTICLE_SIDE_RANGE = 100
const TREE_GAP_X = 100
const TREE_PROPOSAL_GAP = 150
const FOCUS_COL_GAP = 80
const FOCUS_MAX_ROWS = 6
const FOCUS_GRID_COL_STRIDE = NODE_WIDTH + FOCUS_COL_GAP
const TEXT_PREVIEW_LEN = 160
const FALLBACK_VIEWPORT_WIDTH = 1280
const FALLBACK_VIEWPORT_HEIGHT = 800
const DIMMED_OPACITY = 0.12
const COLLIDE_PADDING = 24
const SIM_TICKS = 320

/** Confidence domain for Inferno (70%–100%). */
const CONFIDENCE_DOMAIN_MIN = 0.7
const CONFIDENCE_DOMAIN_MAX = 1
const CONFIDENCE_FALLBACK = 0.85
const EDGE_STROKE_WIDTH = 1

/** Degrees shown by default; widen later when a toggle is added. */
export const DEFAULT_MATCH_DEGREES: MatchDegree[] = ['medio', 'alto']

function truncate(text: string, max = TEXT_PREVIEW_LEN): string {
  const cleaned = text.replace(/\s+/g, ' ').trim()
  if (cleaned.length <= max) return cleaned
  return `${cleaned.slice(0, max).trimEnd()}…`
}

function clamp01(t: number): number {
  return Math.max(0, Math.min(1, t))
}

function confidenceToInferno(confidence: number | null): string {
  const value = confidence ?? CONFIDENCE_FALLBACK
  const t = clamp01(
    (value - CONFIDENCE_DOMAIN_MIN) / (CONFIDENCE_DOMAIN_MAX - CONFIDENCE_DOMAIN_MIN)
  )
  return interpolateInferno(t)
}

function edgeStyle(
  confidence: number | null,
  dimmed: boolean
): { stroke: string, strokeWidth: number, opacity: number } {
  return {
    stroke: confidenceToInferno(confidence),
    strokeWidth: EDGE_STROKE_WIDTH,
    opacity: dimmed ? DIMMED_OPACITY : 1
  }
}

export interface ArticleNodeData {
  sectionId: number
  sectionNumber: string | null
  text: string
  linkCount: number
  side: 'left' | 'right'
  dimmed: boolean
  selected: boolean
  highlighted: boolean
}

export interface ProposalNodeData {
  proposalId: number
  text: string
  linkCount: number
  dimmed: boolean
  highlighted: boolean
  selected: boolean
}

export interface MatchEdgeData {
  matchId: number
  degree: MatchDegree | null
  confidence: number | null
}

interface SimNode extends SimulationNodeDatum {
  id: string
  kind: 'article' | 'proposal'
  linkCount: number
  side?: 'left' | 'right'
}

interface SimLink extends SimulationLinkDatum<SimNode> {
  confidence: number
}

function relatedProposalIds(
  sectionId: number,
  matches: Match[]
): { proposalId: number, confidence: number | null }[] {
  const byProposal = new Map<number, number | null>()
  for (const match of matches) {
    if (match.section_id !== sectionId) continue
    const prev = byProposal.get(match.proposal_id)
    if (prev === undefined || (match.confidence ?? 0) > (prev ?? 0)) {
      byProposal.set(match.proposal_id, match.confidence)
    }
  }
  return [...byProposal.entries()]
    .map(([proposalId, confidence]) => ({ proposalId, confidence }))
    .sort((a, b) => (b.confidence ?? 0) - (a.confidence ?? 0))
}

function linkedArticlesForProposal(
  proposalId: number,
  matches: Match[]
): { sectionId: number, confidence: number | null }[] {
  const bySection = new Map<number, number | null>()
  for (const match of matches) {
    if (match.proposal_id !== proposalId) continue
    const prev = bySection.get(match.section_id)
    if (prev === undefined || (match.confidence ?? 0) > (prev ?? 0)) {
      bySection.set(match.section_id, match.confidence)
    }
  }
  return [...bySection.entries()]
    .map(([sectionId, confidence]) => ({ sectionId, confidence }))
    .sort((a, b) => (b.confidence ?? 0) - (a.confidence ?? 0))
}

function peerProposalsForArticles(
  proposalId: number,
  articleIds: Set<number>,
  matches: Match[]
): { proposalId: number, confidence: number | null }[] {
  const byProposal = new Map<number, number | null>()
  for (const match of matches) {
    if (!articleIds.has(match.section_id)) continue
    if (match.proposal_id === proposalId) continue
    const prev = byProposal.get(match.proposal_id)
    if (prev === undefined || (match.confidence ?? 0) > (prev ?? 0)) {
      byProposal.set(match.proposal_id, match.confidence)
    }
  }
  return [...byProposal.entries()]
    .map(([id, confidence]) => ({ proposalId: id, confidence }))
    .sort((a, b) => (b.confidence ?? 0) - (a.confidence ?? 0))
}

function countLinksBySection(matches: Match[]): Map<number, number> {
  const counts = new Map<number, number>()
  for (const match of matches) {
    counts.set(match.section_id, (counts.get(match.section_id) ?? 0) + 1)
  }
  return counts
}

function countLinksByProposal(matches: Match[]): Map<number, number> {
  const counts = new Map<number, number>()
  for (const match of matches) {
    counts.set(match.proposal_id, (counts.get(match.proposal_id) ?? 0) + 1)
  }
  return counts
}

function median(values: number[]): number {
  if (values.length === 0) return 0
  const sorted = [...values].sort((a, b) => a - b)
  const mid = Math.floor(sorted.length / 2)
  return sorted.length % 2 === 0
    ? ((sorted[mid - 1] ?? 0) + (sorted[mid] ?? 0)) / 2
    : (sorted[mid] ?? 0)
}

function collideRadius(): number {
  return Math.hypot(NODE_WIDTH / 2, NODE_HEIGHT / 2) + COLLIDE_PADDING
}

/** Lay out items in a grid: fill rows top→bottom, then wrap to the next column (max FOCUS_MAX_ROWS). */
function gridPositions(
  count: number,
  originX: number,
  originY: number,
  options: {
    maxRows?: number
    colStride?: number
    rowGap?: number
    /** 1 = columns grow right, -1 = columns grow left */
    direction?: 1 | -1
  } = {}
): Array<{ x: number, y: number }> {
  const maxRows = options.maxRows ?? FOCUS_MAX_ROWS
  const colStride = options.colStride ?? FOCUS_GRID_COL_STRIDE
  const rowGap = options.rowGap ?? TREE_PROPOSAL_GAP
  const direction = options.direction ?? 1
  const positions: Array<{ x: number, y: number }> = []

  for (let i = 0; i < count; i++) {
    const col = Math.floor(i / maxRows)
    const row = i % maxRows
    positions.push({
      x: originX + direction * col * colStride,
      y: originY + row * rowGap
    })
  }

  return positions
}

function runForceLayout(
  sections: Section[],
  proposals: Proposal[],
  matches: Match[],
  viewportWidth: number,
  viewportHeight: number
): Map<string, { x: number, y: number, side?: 'left' | 'right' }> {
  const width = viewportWidth > 0 ? viewportWidth : FALLBACK_VIEWPORT_WIDTH
  const height = viewportHeight > 0 ? viewportHeight : FALLBACK_VIEWPORT_HEIGHT
  const matchable = sections.filter(s => s.is_matchable)
  const sectionLinkCounts = countLinksBySection(matches)
  const proposalLinkCounts = countLinksByProposal(matches)

  const articleCounts = matchable.map(s => sectionLinkCounts.get(s.id) ?? 0)
  const linkMedian = median(articleCounts.filter(c => c > 0).length
    ? articleCounts
    : [0])

  const leftX = COLUMN_INSET
  const rightX = COLUMN_INSET + ARTICLE_SIDE_RANGE
  const centerX = width / 2 - NODE_WIDTH / 2
  const centerY = height / 2
  const articleStep = NODE_HEIGHT + 28

  const simNodes: SimNode[] = []
  const nodeById = new Map<string, SimNode>()

  matchable.forEach((section, index) => {
    const linkCount = sectionLinkCounts.get(section.id) ?? 0
    const side: 'left' | 'right' = linkCount >= linkMedian ? 'left' : 'right'
    const x = side === 'left' ? leftX : rightX
    const y = COLUMN_INSET + index * articleStep
    const node: SimNode = {
      id: `article-${section.id}`,
      kind: 'article',
      linkCount,
      side,
      x,
      y,
      fx: x,
      fy: y
    }
    simNodes.push(node)
    nodeById.set(node.id, node)
  })

  proposals.forEach((proposal, index) => {
    const linkCount = proposalLinkCounts.get(proposal.id) ?? 0
    const node: SimNode = {
      id: `proposal-${proposal.id}`,
      kind: 'proposal',
      linkCount,
      x: centerX + ((index % 7) - 3) * 28,
      y: centerY + Math.floor(index / 7) * 36 - 100
    }
    simNodes.push(node)
    nodeById.set(node.id, node)
  })

  const simLinks: SimLink[] = []
  for (const match of matches) {
    const source = nodeById.get(`article-${match.section_id}`)
    const target = nodeById.get(`proposal-${match.proposal_id}`)
    if (!source || !target) continue
    simLinks.push({
      source,
      target,
      confidence: match.confidence ?? CONFIDENCE_FALLBACK
    })
  }

  const simulation = forceSimulation(simNodes)
    .force(
      'link',
      forceLink<SimNode, SimLink>(simLinks)
        .id(d => d.id)
        .distance(d => 140 + (1 - d.confidence) * 220)
        .strength(d => 0.25 + d.confidence * 0.75)
    )
    .force(
      'charge',
      forceManyBody<SimNode>()
        .strength(d => {
          if (d.kind === 'article') return 0
          return -100 - d.linkCount * 20
        })
        .distanceMax(640)
    )
    .force(
      'collide',
      forceCollide<SimNode>()
        .radius(collideRadius())
        .strength(1)
        .iterations(4)
    )
    .force(
      'x',
      forceX<SimNode>(centerX)
        .strength(d => (d.kind === 'proposal' ? 0.06 + Math.min(d.linkCount, 8) * 0.02 : 0))
    )
    .force(
      'y',
      forceY<SimNode>(centerY)
        .strength(d => (d.kind === 'proposal' ? 0.04 : 0))
    )
    .stop()

  for (let i = 0; i < SIM_TICKS; i++) simulation.tick()

  const positions = new Map<string, { x: number, y: number, side?: 'left' | 'right' }>()
  for (const node of simNodes) {
    positions.set(node.id, {
      x: node.x ?? 0,
      y: node.y ?? 0,
      side: node.side
    })
  }
  return positions
}

function buildGraph(
  sections: Section[],
  proposals: Proposal[],
  matches: Match[],
  positions: Map<string, { x: number, y: number, side?: 'left' | 'right' }>,
  selectedArticleId: number | null,
  selectedProposalId: number | null
): { nodes: Node[], edges: Edge[] } {
  const matchable = sections.filter(s => s.is_matchable)
  const sectionLinkCounts = countLinksBySection(matches)
  const proposalLinkCounts = countLinksByProposal(matches)
  const hasFocus = selectedArticleId !== null || selectedProposalId !== null

  // --- Article focus: related proposals in a grid (max 6 rows, then new columns) ---
  const articleRelated = selectedArticleId === null
    ? []
    : relatedProposalIds(selectedArticleId, matches)
  const articleRelatedSet = new Set(articleRelated.map(r => r.proposalId))

  const selectedArticlePos = selectedArticleId === null
    ? null
    : positions.get(`article-${selectedArticleId}`)
  const selectedSide = selectedArticlePos?.side ?? 'left'
  const articleTreeX = selectedSide === 'left'
    ? (selectedArticlePos?.x ?? COLUMN_INSET) + NODE_WIDTH + TREE_GAP_X
    : (selectedArticlePos?.x ?? COLUMN_INSET) - NODE_WIDTH - TREE_GAP_X
  const articleRowsUsed = Math.min(articleRelated.length, FOCUS_MAX_ROWS)
  const articleTreeStartY = (selectedArticlePos?.y ?? 0)
    - (Math.max(articleRowsUsed - 1, 0) * TREE_PROPOSAL_GAP) / 2
  const articleRelatedGrid = gridPositions(
    articleRelated.length,
    articleTreeX,
    articleTreeStartY,
    { direction: selectedSide === 'left' ? 1 : -1 }
  )
  const articleRelatedPos = new Map<number, { x: number, y: number }>()
  articleRelated.forEach((r, i) => {
    const cell = articleRelatedGrid[i]
    if (cell) articleRelatedPos.set(r.proposalId, cell)
  })

  // --- Proposal focus: proposal | articles | peer proposals ---
  const linkedArticles = selectedProposalId === null
    ? []
    : linkedArticlesForProposal(selectedProposalId, matches)
  const linkedArticleSet = new Set(linkedArticles.map(a => a.sectionId))
  const peerProposals = selectedProposalId === null
    ? []
    : peerProposalsForArticles(selectedProposalId, linkedArticleSet, matches)
  const peerProposalSet = new Set(peerProposals.map(p => p.proposalId))

  const focusProposalX = COLUMN_INSET
  const focusArticlesX = COLUMN_INSET + NODE_WIDTH + FOCUS_COL_GAP
  const articlesCols = Math.max(1, Math.ceil(linkedArticles.length / FOCUS_MAX_ROWS))
  const focusPeersX = focusArticlesX + articlesCols * FOCUS_GRID_COL_STRIDE

  const linkedArticleGrid = gridPositions(
    linkedArticles.length,
    focusArticlesX,
    COLUMN_INSET
  )
  const linkedArticlePos = new Map<number, { x: number, y: number }>()
  linkedArticles.forEach((a, i) => {
    const cell = linkedArticleGrid[i]
    if (cell) linkedArticlePos.set(a.sectionId, cell)
  })

  const peerProposalGrid = gridPositions(
    peerProposals.length,
    focusPeersX,
    COLUMN_INSET
  )
  const peerProposalPos = new Map<number, { x: number, y: number }>()
  peerProposals.forEach((p, i) => {
    const cell = peerProposalGrid[i]
    if (cell) peerProposalPos.set(p.proposalId, cell)
  })

  const articleNodes: Node<ArticleNodeData>[] = matchable.map((section) => {
    const id = `article-${section.id}`
    const pos = positions.get(id) ?? { x: COLUMN_INSET, y: 0, side: 'left' as const }
    const selected = section.id === selectedArticleId
    const highlighted = linkedArticleSet.has(section.id)
    const dimmed = hasFocus && !selected && !highlighted
    const linkCount = sectionLinkCounts.get(section.id) ?? 0
    const side = pos.side ?? 'left'

    let position = { x: pos.x, y: pos.y }
    if (selectedProposalId !== null && highlighted) {
      position = linkedArticlePos.get(section.id) ?? position
    }

    return {
      id,
      type: 'article',
      position,
      connectable: false,
      draggable: false,
      zIndex: selected || highlighted ? 10 : 1,
      style: { opacity: dimmed ? DIMMED_OPACITY : 1 },
      data: {
        sectionId: section.id,
        sectionNumber: section.section_number,
        text: section.clear_language || section.text,
        linkCount,
        side,
        dimmed,
        selected,
        highlighted
      }
    }
  })

  const proposalNodes: Node<ProposalNodeData>[] = proposals.map((proposal) => {
    const id = `proposal-${proposal.id}`
    const pos = positions.get(id) ?? { x: 0, y: 0 }
    const selected = proposal.id === selectedProposalId
    const highlighted = articleRelatedSet.has(proposal.id) || peerProposalSet.has(proposal.id)
    const dimmed = hasFocus && !selected && !highlighted
    const linkCount = proposalLinkCounts.get(proposal.id) ?? 0

    let position = { x: pos.x, y: pos.y }
    if (selectedArticleId !== null && highlighted) {
      position = articleRelatedPos.get(proposal.id) ?? position
    } else if (selectedProposalId !== null && selected) {
      position = { x: focusProposalX, y: COLUMN_INSET }
    } else if (selectedProposalId !== null && peerProposalSet.has(proposal.id)) {
      position = peerProposalPos.get(proposal.id) ?? position
    }

    return {
      id,
      type: 'proposal',
      position,
      connectable: false,
      zIndex: selected || highlighted ? 10 : 1,
      style: { opacity: dimmed ? DIMMED_OPACITY : 1 },
      data: {
        proposalId: proposal.id,
        text: truncate(proposal.text),
        linkCount,
        dimmed,
        highlighted,
        selected
      }
    }
  })

  const nodes: Node[] = [...articleNodes, ...proposalNodes]
  const nodeIds = new Set(nodes.map(n => n.id))
  const articleSideById = new Map(
    articleNodes.map(n => [n.id, (n.data as ArticleNodeData).side])
  )

  const edges: Edge<MatchEdgeData>[] = []
  for (const match of matches) {
    const source = `article-${match.section_id}`
    const target = `proposal-${match.proposal_id}`
    if (!nodeIds.has(source) || !nodeIds.has(target)) continue

    let relatedEdge = false
    if (selectedArticleId !== null) {
      relatedEdge = match.section_id === selectedArticleId
    } else if (selectedProposalId !== null) {
      relatedEdge = linkedArticleSet.has(match.section_id)
        && (match.proposal_id === selectedProposalId
          || peerProposalSet.has(match.proposal_id))
    }

    const dimmed = hasFocus && !relatedEdge
    const side = articleSideById.get(source) ?? 'left'

    let sourceHandle = side === 'left' ? 'right' : 'left'
    let targetHandle = side === 'left' ? 'left' : 'right'
    if (selectedProposalId !== null && relatedEdge) {
      const proposalOnLeft = match.proposal_id === selectedProposalId
      sourceHandle = proposalOnLeft ? 'left' : 'right'
      targetHandle = proposalOnLeft ? 'right' : 'left'
    }

    edges.push({
      id: `match-${match.id}`,
      source,
      target,
      sourceHandle,
      targetHandle,
      type: 'default',
      animated: relatedEdge,
      zIndex: relatedEdge ? 5 : 0,
      style: edgeStyle(match.confidence, dimmed),
      data: {
        matchId: match.id,
        degree: match.degree,
        confidence: match.confidence
      }
    })
  }

  return { nodes, edges }
}

export function useExperimentalGraph(
  sections: MaybeRefOrGetter<Section[] | null | undefined>,
  proposals: MaybeRefOrGetter<Proposal[] | null | undefined>,
  matches: MaybeRefOrGetter<Match[] | null | undefined>,
  viewportWidth: MaybeRefOrGetter<number> = FALLBACK_VIEWPORT_WIDTH,
  viewportHeight: MaybeRefOrGetter<number> = FALLBACK_VIEWPORT_HEIGHT
) {
  const nodes = ref<Node[]>([])
  const edges = ref<Edge[]>([])
  const selectedArticleId = ref<number | null>(null)
  const selectedProposalId = ref<number | null>(null)
  const basePositions = ref<Map<string, { x: number, y: number, side?: 'left' | 'right' }>>(
    new Map()
  )

  const hasSelection = computed(
    () => selectedArticleId.value !== null || selectedProposalId.value !== null
  )

  function computeForcePositions() {
    const secs = toValue(sections)
    const props = toValue(proposals)
    const matchList = toValue(matches)
    if (!secs || !props || !matchList) return
    basePositions.value = runForceLayout(
      secs,
      props,
      matchList,
      toValue(viewportWidth),
      toValue(viewportHeight)
    )
  }

  function applyGraph() {
    const secs = toValue(sections)
    const props = toValue(proposals)
    const matchList = toValue(matches)
    if (!secs || !props || !matchList || basePositions.value.size === 0) return
    const graph = buildGraph(
      secs,
      props,
      matchList,
      basePositions.value,
      selectedArticleId.value,
      selectedProposalId.value
    )
    nodes.value = graph.nodes
    edges.value = graph.edges
  }

  watch(
    () => [
      toValue(sections),
      toValue(proposals),
      toValue(matches),
      toValue(viewportWidth),
      toValue(viewportHeight)
    ] as const,
    () => {
      computeForcePositions()
      applyGraph()
    },
    { immediate: true }
  )

  watch([selectedArticleId, selectedProposalId], () => applyGraph())

  function toggleArticle(sectionId: number) {
    selectedProposalId.value = null
    selectedArticleId.value
      = selectedArticleId.value === sectionId ? null : sectionId
  }

  function toggleProposal(proposalId: number) {
    selectedArticleId.value = null
    selectedProposalId.value
      = selectedProposalId.value === proposalId ? null : proposalId
  }

  function clearSelection() {
    selectedArticleId.value = null
    selectedProposalId.value = null
  }

  return {
    nodes,
    edges,
    selectedArticleId,
    selectedProposalId,
    hasSelection,
    toggleArticle,
    toggleProposal,
    clearSelection
  }
}
