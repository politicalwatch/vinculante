import { interpolateInferno } from 'd3-scale-chromatic'
import type { Edge, Node } from '@vue-flow/core'
import type { Match, MatchDegree, Proposal, Section } from '~/types/api'

const NODE_WIDTH = 340
const COLUMN_INSET = 48
const MIN_COLUMN_GAP = 280
const ARTICLE_GAP = 160
const PROPOSAL_GAP = 140
const TREE_GAP_X = 100
const TREE_PROPOSAL_GAP = 150
const TEXT_PREVIEW_LEN = 160
const FALLBACK_VIEWPORT_WIDTH = 1280
const DIMMED_OPACITY = 0.12

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

/** Map confidence ∈ [0.7, 1] → Inferno sequential color (d3.interpolateInferno). */
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

function articleColumnX(): number {
  return COLUMN_INSET
}

function proposalColumnX(viewportWidth: number): number {
  const width = viewportWidth > 0 ? viewportWidth : FALLBACK_VIEWPORT_WIDTH
  return Math.max(
    COLUMN_INSET + NODE_WIDTH + MIN_COLUMN_GAP,
    width - NODE_WIDTH - COLUMN_INSET
  )
}

export interface ArticleNodeData {
  sectionId: number
  sectionNumber: string | null
  text: string
  dimmed: boolean
  selected: boolean
}

export interface ProposalNodeData {
  proposalId: number
  text: string
  dimmed: boolean
  highlighted: boolean
}

export interface MatchEdgeData {
  matchId: number
  degree: MatchDegree | null
  confidence: number | null
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

function buildGraph(
  sections: Section[],
  proposals: Proposal[],
  matches: Match[],
  viewportWidth: number,
  selectedArticleId: number | null
): { nodes: Node[], edges: Edge[] } {
  const articleX = articleColumnX()
  const proposalX = proposalColumnX(viewportWidth)
  const matchable = sections.filter(s => s.is_matchable)

  const related = selectedArticleId === null
    ? []
    : relatedProposalIds(selectedArticleId, matches)
  const relatedSet = new Set(related.map(r => r.proposalId))

  const selectedArticleIndex = selectedArticleId === null
    ? -1
    : matchable.findIndex(s => s.id === selectedArticleId)
  const selectedArticleY = selectedArticleIndex >= 0
    ? selectedArticleIndex * ARTICLE_GAP
    : 0

  const treeX = articleX + NODE_WIDTH + TREE_GAP_X
  const treeStartY = selectedArticleY - ((related.length - 1) * TREE_PROPOSAL_GAP) / 2
  const relatedYByProposal = new Map<number, number>()
  related.forEach((r, i) => {
    relatedYByProposal.set(r.proposalId, treeStartY + i * TREE_PROPOSAL_GAP)
  })

  const articleNodes: Node<ArticleNodeData>[] = matchable.map((section, index) => {
    const selected = section.id === selectedArticleId
    const dimmed = selectedArticleId !== null && !selected
    return {
      id: `article-${section.id}`,
      type: 'article',
      position: { x: articleX, y: index * ARTICLE_GAP },
      connectable: false,
      zIndex: selected ? 10 : 1,
      style: { opacity: dimmed ? DIMMED_OPACITY : 1 },
      data: {
        sectionId: section.id,
        sectionNumber: section.section_number,
        text: truncate(section.clear_language || section.text),
        dimmed,
        selected
      }
    }
  })

  const proposalNodes: Node<ProposalNodeData>[] = proposals.map((proposal, index) => {
    const highlighted = relatedSet.has(proposal.id)
    const dimmed = selectedArticleId !== null && !highlighted
    const position = highlighted
      ? { x: treeX, y: relatedYByProposal.get(proposal.id) ?? index * PROPOSAL_GAP }
      : { x: proposalX, y: index * PROPOSAL_GAP }

    return {
      id: `proposal-${proposal.id}`,
      type: 'proposal',
      position,
      connectable: false,
      zIndex: highlighted ? 10 : 1,
      style: { opacity: dimmed ? DIMMED_OPACITY : 1 },
      data: {
        proposalId: proposal.id,
        text: truncate(proposal.text),
        dimmed,
        highlighted
      }
    }
  })

  const nodes: Node[] = [...articleNodes, ...proposalNodes]
  const nodeIds = new Set(nodes.map(n => n.id))

  const edges: Edge<MatchEdgeData>[] = []
  for (const match of matches) {
    const source = `article-${match.section_id}`
    const target = `proposal-${match.proposal_id}`
    if (!nodeIds.has(source) || !nodeIds.has(target)) continue

    const relatedEdge = selectedArticleId !== null
      && match.section_id === selectedArticleId
    const dimmed = selectedArticleId !== null && !relatedEdge

    edges.push({
      id: `match-${match.id}`,
      source,
      target,
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
  viewportWidth: MaybeRefOrGetter<number> = FALLBACK_VIEWPORT_WIDTH
) {
  const nodes = ref<Node[]>([])
  const edges = ref<Edge[]>([])
  const selectedArticleId = ref<number | null>(null)

  function rebuild() {
    const secs = toValue(sections)
    const props = toValue(proposals)
    const matchList = toValue(matches)
    if (!secs || !props || !matchList) return
    const graph = buildGraph(
      secs,
      props,
      matchList,
      toValue(viewportWidth),
      selectedArticleId.value
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
      selectedArticleId.value
    ] as const,
    () => rebuild(),
    { immediate: true }
  )

  function selectArticle(sectionId: number | null) {
    selectedArticleId.value = sectionId
  }

  function toggleArticle(sectionId: number) {
    selectedArticleId.value
      = selectedArticleId.value === sectionId ? null : sectionId
  }

  function clearSelection() {
    selectedArticleId.value = null
  }

  return {
    nodes,
    edges,
    selectedArticleId,
    selectArticle,
    toggleArticle,
    clearSelection
  }
}
