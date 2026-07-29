import {
  forceCenter,
  forceCollide,
  forceLink,
  forceManyBody,
  forceSimulation,
  forceX,
  forceY,
  type Simulation,
  type SimulationLinkDatum,
  type SimulationNodeDatum
} from 'd3-force'
import { interpolateCividis } from 'd3-scale-chromatic'
import type { Match, MatchDegree, Proposal, Section } from '~/types/api'
import {
  createDefaultFilters,
  FETCH_MATCH_DEGREES,
  type GraphFilters,
  type GraphTotalCounts,
  type GraphVisibleCounts,
  type LinkCountBounds
} from '~/composables/useExperimentalGraph'

export { FETCH_MATCH_DEGREES, createDefaultFilters }
export type { GraphFilters, GraphTotalCounts, GraphVisibleCounts, LinkCountBounds }

const FALLBACK_VIEWPORT_WIDTH = 1280
const FALLBACK_VIEWPORT_HEIGHT = 800
const DIMMED_OPACITY = 0.18
const ARTICLE_R_MIN = 14
const ARTICLE_R_MAX = 42
const HEXAGON_SIZE_MIN = 12
const HEXAGON_SIZE_MAX = 36
const CIRCLE_ARTICLE_R_MIN = 8
const CIRCLE_ARTICLE_R_MAX = 22
const CIRCLE_HEXAGON_SIZE_MIN = 7
const CIRCLE_HEXAGON_SIZE_MAX = 18
const CIRCLE_PADDING = 24
const CIRCLE_INNER_RATIO = 0.48
const COLLIDE_PADDING = 6
const CONFIDENCE_DOMAIN_MIN = 0.7
const CONFIDENCE_DOMAIN_MAX = 1
const CONFIDENCE_FALLBACK = 0.85

export type BallLayoutMode = 'force' | 'circles'
export type BallNodeKind = 'article' | 'proposal'

export interface BallSimNode extends SimulationNodeDatum {
  id: string
  kind: BallNodeKind
  entityId: number
  linkCount: number
  label: string
  text: string
  /** Circle radius (articles) or hexagon radius (proposals). */
  size: number
  fill: string
  selected: boolean
  highlighted: boolean
  dimmed: boolean
}

export interface BallSimLink extends SimulationLinkDatum<BallSimNode> {
  id: string
  matchId: number
  confidence: number
  stroke: string
  animated: boolean
  dimmed: boolean
}

export interface BallSelectedDetail {
  kind: BallNodeKind
  id: number
  title: string
  text: string
  linkCount: number
}

const DEGREE_RANK: Record<string, number> = {
  alto: 3,
  medio: 2,
  bajo: 1,
  ninguno: 0
}

function matchesDegreeFloor(degree: MatchDegree | null, floor: GraphFilters['degreeFloor']): boolean {
  if (!degree || degree === 'ninguno') return false
  return (DEGREE_RANK[degree] ?? 0) >= (DEGREE_RANK[floor] ?? 0)
}

function inLinkRange(count: number, min: number, max: number | null): boolean {
  if (count < min) return false
  if (max !== null && count > max) return false
  return true
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

function applyGraphFilters(
  sections: Section[],
  proposals: Proposal[],
  matches: Match[],
  filters: GraphFilters
): {
  sections: Section[]
  proposals: Proposal[]
  matches: Match[]
  linkCountBounds: LinkCountBounds
  totals: GraphTotalCounts
  visible: GraphVisibleCounts
} {
  const matchable = sections.filter(s => s.is_matchable)
  const degreeMatches = matches.filter(m =>
    matchesDegreeFloor(m.degree, filters.degreeFloor)
  )

  const sectionCounts = countLinksBySection(degreeMatches)
  const proposalCounts = countLinksByProposal(degreeMatches)

  const articleMax = matchable.reduce(
    (max, s) => Math.max(max, sectionCounts.get(s.id) ?? 0),
    0
  )
  const proposalMax = proposals.reduce(
    (max, p) => Math.max(max, proposalCounts.get(p.id) ?? 0),
    0
  )

  const filteredSections = matchable.filter(s =>
    inLinkRange(
      sectionCounts.get(s.id) ?? 0,
      filters.articleLinksMin,
      filters.articleLinksMax
    )
  )

  const filteredProposals = proposals.filter((p) => {
    if (
      filters.proposalAuthorType !== 'all'
      && p.author_type !== filters.proposalAuthorType
    ) {
      return false
    }
    return inLinkRange(
      proposalCounts.get(p.id) ?? 0,
      filters.proposalLinksMin,
      filters.proposalLinksMax
    )
  })

  const sectionIds = new Set(filteredSections.map(s => s.id))
  const proposalIds = new Set(filteredProposals.map(p => p.id))
  const filteredMatches = degreeMatches.filter(
    m => sectionIds.has(m.section_id) && proposalIds.has(m.proposal_id)
  )

  return {
    sections: filteredSections,
    proposals: filteredProposals,
    matches: filteredMatches,
    linkCountBounds: { articleMax, proposalMax },
    totals: {
      articles: matchable.length,
      proposals: proposals.length,
      matches: degreeMatches.length
    },
    visible: {
      articles: filteredSections.length,
      proposals: filteredProposals.length,
      matches: filteredMatches.length
    }
  }
}

function clamp01(t: number): number {
  return Math.max(0, Math.min(1, t))
}

function confidenceToInferno(confidence: number | null): string {
  const value = confidence ?? CONFIDENCE_FALLBACK
  const t = clamp01(
    (value - CONFIDENCE_DOMAIN_MIN) / (CONFIDENCE_DOMAIN_MAX - CONFIDENCE_DOMAIN_MIN)
  )
  return interpolateCividis(t)
}

function linkCountScale(
  count: number,
  max: number,
  minOut: number,
  maxOut: number
): number {
  if (max <= 0) return (minOut + maxOut) / 2
  const t = clamp01(count / max)
  return minOut + t * (maxOut - minOut)
}

function articleFill(count: number, max: number): string {
  if (max <= 0) return interpolateCividis(0.35)
  return interpolateCividis(0.25 + clamp01(count / max) * 0.65)
}

function nodeRadius(node: BallSimNode): number {
  return node.size
}

function resolveLinkEndpoint(
  end: string | number | BallSimNode | undefined,
  byId: Map<string, BallSimNode>
): BallSimNode | null {
  if (end == null) return null
  if (typeof end === 'object') return end
  return byId.get(String(end)) ?? null
}

/** Quadratic Bezier with a perpendicular bulge so overlapping chords fan out. */
export function bezierPath(
  x1: number,
  y1: number,
  x2: number,
  y2: number,
  curveIndex = 0
): string {
  const mx = (x1 + x2) / 2
  const my = (y1 + y2) / 2
  const dx = x2 - x1
  const dy = y2 - y1
  const len = Math.hypot(dx, dy) || 1
  const nx = -dy / len
  const ny = dx / len
  const bulge = 28 + (curveIndex % 5) * 12
  const sign = curveIndex % 2 === 0 ? 1 : -1
  const cx = mx + nx * bulge * sign
  const cy = my + ny * bulge * sign
  return `M${x1},${y1} Q${cx},${cy} ${x2},${y2}`
}

/** Pointy-top hexagon; `size` is the circumradius. */
export function hexagonPoints(x: number, y: number, size: number): string {
  const points: string[] = []
  for (let i = 0; i < 6; i++) {
    const angle = -Math.PI / 2 + (i * Math.PI) / 3
    points.push(`${x + size * Math.cos(angle)},${y + size * Math.sin(angle)}`)
  }
  return points.join(' ')
}

function compareSectionOrder(a: Section, b: Section): number {
  const an = a.section_number
  const bn = b.section_number
  if (an != null && bn != null) {
    const byNumber = an.localeCompare(bn, undefined, { numeric: true, sensitivity: 'base' })
    if (byNumber !== 0) return byNumber
  } else if (an != null) {
    return -1
  } else if (bn != null) {
    return 1
  }
  return a.id - b.id
}

function ringPosition(
  index: number,
  count: number,
  cx: number,
  cy: number,
  radius: number
): { x: number, y: number } {
  const angle = -Math.PI / 2 + (index * 2 * Math.PI) / Math.max(count, 1)
  return {
    x: cx + radius * Math.cos(angle),
    y: cy + radius * Math.sin(angle)
  }
}

export function useExperimentalBallGraph(
  sections: MaybeRefOrGetter<Section[] | null | undefined>,
  proposals: MaybeRefOrGetter<Proposal[] | null | undefined>,
  matches: MaybeRefOrGetter<Match[] | null | undefined>,
  viewportWidth: MaybeRefOrGetter<number> = FALLBACK_VIEWPORT_WIDTH,
  viewportHeight: MaybeRefOrGetter<number> = FALLBACK_VIEWPORT_HEIGHT
) {
  const simNodes = ref<BallSimNode[]>([])
  const simLinks = ref<BallSimLink[]>([])
  const layoutMode = ref<BallLayoutMode>('force')
  const selectedArticleId = ref<number | null>(null)
  const selectedProposalId = ref<number | null>(null)
  const filters = reactive<GraphFilters>(createDefaultFilters())
  const linkCountBounds = ref<LinkCountBounds>({ articleMax: 0, proposalMax: 0 })
  const totals = ref<GraphTotalCounts>({ articles: 0, proposals: 0, matches: 0 })
  const visible = ref<GraphVisibleCounts>({ articles: 0, proposals: 0, matches: 0 })

  let simulation: Simulation<BallSimNode, BallSimLink> | null = null
  let internalNodes: BallSimNode[] = []
  let internalLinks: BallSimLink[] = []
  const nodeById = new Map<string, BallSimNode>()

  const hasSelection = computed(
    () => selectedArticleId.value !== null || selectedProposalId.value !== null
  )

  const hasActiveFilters = computed(() => {
    const defaults = createDefaultFilters()
    return filters.degreeFloor !== defaults.degreeFloor
      || filters.articleLinksMin !== defaults.articleLinksMin
      || filters.articleLinksMax !== defaults.articleLinksMax
      || filters.proposalAuthorType !== defaults.proposalAuthorType
      || filters.proposalLinksMin !== defaults.proposalLinksMin
      || filters.proposalLinksMax !== defaults.proposalLinksMax
  })

  const selectedDetail = computed<BallSelectedDetail | null>(() => {
    if (selectedArticleId.value !== null) {
      const node = internalNodes.find(
        n => n.kind === 'article' && n.entityId === selectedArticleId.value
      )
      if (!node) return null
      return {
        kind: 'article',
        id: node.entityId,
        title: `Artículo ${node.label}`,
        text: node.text,
        linkCount: node.linkCount
      }
    }
    if (selectedProposalId.value !== null) {
      const node = internalNodes.find(
        n => n.kind === 'proposal' && n.entityId === selectedProposalId.value
      )
      if (!node) return null
      return {
        kind: 'proposal',
        id: node.entityId,
        title: `Propuesta #${node.entityId}`,
        text: node.text,
        linkCount: node.linkCount
      }
    }
    return null
  })

  const neighborIds = computed(() => {
    const ids = new Set<string>()
    if (selectedArticleId.value !== null) {
      const articleId = `article-${selectedArticleId.value}`
      ids.add(articleId)
      for (const link of internalLinks) {
        const source = resolveLinkEndpoint(link.source, nodeById)
        const target = resolveLinkEndpoint(link.target, nodeById)
        if (source?.id === articleId && target) ids.add(target.id)
        if (target?.id === articleId && source) ids.add(source.id)
      }
    } else if (selectedProposalId.value !== null) {
      const proposalId = `proposal-${selectedProposalId.value}`
      ids.add(proposalId)
      for (const link of internalLinks) {
        const source = resolveLinkEndpoint(link.source, nodeById)
        const target = resolveLinkEndpoint(link.target, nodeById)
        if (source?.id === proposalId && target) ids.add(target.id)
        if (target?.id === proposalId && source) ids.add(source.id)
      }
    }
    return ids
  })

  function getFilteredData() {
    const secs = toValue(sections)
    const props = toValue(proposals)
    const matchList = toValue(matches)
    if (!secs || !props || !matchList) return null
    return applyGraphFilters(secs, props, matchList, filters)
  }

  function clampFiltersToBounds(bounds: LinkCountBounds) {
    if (filters.articleLinksMin > bounds.articleMax) {
      filters.articleLinksMin = bounds.articleMax
    }
    if (filters.articleLinksMax !== null) {
      if (filters.articleLinksMax >= bounds.articleMax) {
        filters.articleLinksMax = null
      } else if (filters.articleLinksMax < filters.articleLinksMin) {
        filters.articleLinksMax = filters.articleLinksMin
      }
    }
    if (filters.proposalLinksMin > bounds.proposalMax) {
      filters.proposalLinksMin = bounds.proposalMax
    }
    if (filters.proposalLinksMax !== null) {
      if (filters.proposalLinksMax >= bounds.proposalMax) {
        filters.proposalLinksMax = null
      } else if (filters.proposalLinksMax < filters.proposalLinksMin) {
        filters.proposalLinksMax = filters.proposalLinksMin
      }
    }
  }

  function clearStaleSelection(filtered: NonNullable<ReturnType<typeof getFilteredData>>) {
    if (
      selectedArticleId.value !== null
      && !filtered.sections.some(s => s.id === selectedArticleId.value)
    ) {
      selectedArticleId.value = null
    }
    if (
      selectedProposalId.value !== null
      && !filtered.proposals.some(p => p.id === selectedProposalId.value)
    ) {
      selectedProposalId.value = null
    }
  }

  function publishSnapshot() {
    const focus = hasSelection.value
    const neighbors = neighborIds.value

    for (const node of internalNodes) {
      const selected
        = (node.kind === 'article' && node.entityId === selectedArticleId.value)
          || (node.kind === 'proposal' && node.entityId === selectedProposalId.value)
      const highlighted = focus && neighbors.has(node.id) && !selected
      node.selected = selected
      node.highlighted = highlighted
      node.dimmed = focus && !neighbors.has(node.id)
    }

    for (const link of internalLinks) {
      const source = resolveLinkEndpoint(link.source, nodeById)
      const target = resolveLinkEndpoint(link.target, nodeById)
      let isRelated = false
      if (source && target && selectedArticleId.value !== null) {
        isRelated
          = (source.kind === 'article' && source.entityId === selectedArticleId.value)
            || (target.kind === 'article' && target.entityId === selectedArticleId.value)
      } else if (source && target && selectedProposalId.value !== null) {
        isRelated
          = (source.kind === 'proposal' && source.entityId === selectedProposalId.value)
            || (target.kind === 'proposal' && target.entityId === selectedProposalId.value)
      }
      link.animated = isRelated
      link.dimmed = focus && !isRelated
    }

    simNodes.value = internalNodes.map(n => ({ ...n }))
    simLinks.value = internalLinks.map(l => ({
      ...l,
      source: typeof l.source === 'object' ? { ...l.source } : l.source,
      target: typeof l.target === 'object' ? { ...l.target } : l.target
    }))
  }

  function onTick() {
    publishSnapshot()
  }

  function stopSimulation() {
    simulation?.stop()
    simulation = null
  }

  function rebuildSimulation() {
    let filtered = getFilteredData()
    if (!filtered) {
      stopSimulation()
      internalNodes = []
      internalLinks = []
      nodeById.clear()
      simNodes.value = []
      simLinks.value = []
      return
    }

    clampFiltersToBounds(filtered.linkCountBounds)
    filtered = getFilteredData()
    if (!filtered) return

    linkCountBounds.value = filtered.linkCountBounds
    totals.value = filtered.totals
    visible.value = filtered.visible
    clearStaleSelection(filtered)

    const width = toValue(viewportWidth) > 0 ? toValue(viewportWidth) : FALLBACK_VIEWPORT_WIDTH
    const height = toValue(viewportHeight) > 0 ? toValue(viewportHeight) : FALLBACK_VIEWPORT_HEIGHT
    const cx = width / 2
    const cy = height / 2
    const isCircles = layoutMode.value === 'circles'

    const sectionCounts = countLinksBySection(filtered.matches)
    const proposalCounts = countLinksByProposal(filtered.matches)
    const articleMax = Math.max(
      1,
      ...filtered.sections.map(s => sectionCounts.get(s.id) ?? 0)
    )
    const proposalMax = Math.max(
      1,
      ...filtered.proposals.map(p => proposalCounts.get(p.id) ?? 0)
    )

    const articleRMin = isCircles ? CIRCLE_ARTICLE_R_MIN : ARTICLE_R_MIN
    const articleRMax = isCircles ? CIRCLE_ARTICLE_R_MAX : ARTICLE_R_MAX
    const hexMin = isCircles ? CIRCLE_HEXAGON_SIZE_MIN : HEXAGON_SIZE_MIN
    const hexMax = isCircles ? CIRCLE_HEXAGON_SIZE_MAX : HEXAGON_SIZE_MAX

    const prevPos = new Map(
      internalNodes.map(n => [n.id, { x: n.x ?? cx, y: n.y ?? cy }])
    )

    stopSimulation()
    nodeById.clear()

    const orderedSections = isCircles
      ? [...filtered.sections].sort(compareSectionOrder)
      : filtered.sections
    const orderedProposals = isCircles
      ? [...filtered.proposals].sort((a, b) => a.id - b.id)
      : filtered.proposals

    internalNodes = []
    orderedSections.forEach((section, index) => {
      const linkCount = sectionCounts.get(section.id) ?? 0
      const id = `article-${section.id}`
      const prev = prevPos.get(id)
      const node: BallSimNode = {
        id,
        kind: 'article',
        entityId: section.id,
        linkCount,
        label: section.section_number ?? String(section.id),
        text: section.clear_language || section.text,
        size: linkCountScale(linkCount, articleMax, articleRMin, articleRMax),
        fill: articleFill(linkCount, articleMax),
        selected: false,
        highlighted: false,
        dimmed: false,
        x: prev?.x ?? cx + ((index % 8) - 3.5) * 36,
        y: prev?.y ?? cy + Math.floor(index / 8) * 36 - 80
      }
      internalNodes.push(node)
      nodeById.set(id, node)
    })

    orderedProposals.forEach((proposal, index) => {
      const linkCount = proposalCounts.get(proposal.id) ?? 0
      const id = `proposal-${proposal.id}`
      const prev = prevPos.get(id)
      const node: BallSimNode = {
        id,
        kind: 'proposal',
        entityId: proposal.id,
        linkCount,
        label: `#${proposal.id}`,
        text: proposal.text,
        size: linkCountScale(linkCount, proposalMax, hexMin, hexMax),
        fill: '#d97706',
        selected: false,
        highlighted: false,
        dimmed: false,
        x: prev?.x ?? cx + ((index % 9) - 4) * 28,
        y: prev?.y ?? cy + Math.floor(index / 9) * 32 + 40
      }
      internalNodes.push(node)
      nodeById.set(id, node)
    })

    internalLinks = []
    for (const match of filtered.matches) {
      const source = nodeById.get(`article-${match.section_id}`)
      const target = nodeById.get(`proposal-${match.proposal_id}`)
      if (!source || !target) continue
      internalLinks.push({
        id: `match-${match.id}`,
        matchId: match.id,
        source,
        target,
        confidence: match.confidence ?? CONFIDENCE_FALLBACK,
        stroke: confidenceToInferno(match.confidence),
        animated: false,
        dimmed: false
      })
    }

    visible.value = {
      articles: filtered.visible.articles,
      proposals: filtered.visible.proposals,
      matches: internalLinks.length
    }

    if (isCircles) {
      applyCircleLayout(cx, cy, width, height, articleRMax, hexMax)
    } else {
      applyForceLayout(cx, cy)
    }
  }

  function applyCircleLayout(
    cx: number,
    cy: number,
    width: number,
    height: number,
    articleRMax: number,
    hexMax: number
  ) {
    const maxNodeExtent = Math.max(articleRMax, hexMax)
    const rOuter = Math.max(
      40,
      Math.min(width, height) / 2 - CIRCLE_PADDING - maxNodeExtent
    )
    const rInner = rOuter * CIRCLE_INNER_RATIO

    const articles = internalNodes.filter(n => n.kind === 'article')
    const proposals = internalNodes.filter(n => n.kind === 'proposal')

    articles.forEach((node, index) => {
      const pos = ringPosition(index, articles.length, cx, cy, rInner)
      node.x = pos.x
      node.y = pos.y
      node.fx = pos.x
      node.fy = pos.y
      node.vx = 0
      node.vy = 0
    })

    proposals.forEach((node, index) => {
      const pos = ringPosition(index, proposals.length, cx, cy, rOuter)
      node.x = pos.x
      node.y = pos.y
      node.fx = pos.x
      node.fy = pos.y
      node.vx = 0
      node.vy = 0
    })

    publishSnapshot()
  }

  function applyForceLayout(cx: number, cy: number) {
    for (const node of internalNodes) {
      node.fx = null
      node.fy = null
    }

    simulation = forceSimulation(internalNodes)
      .force(
        'link',
        forceLink<BallSimNode, BallSimLink>(internalLinks)
          .id(d => d.id)
          .distance(d => 80 + (1 - d.confidence) * 160)
          .strength(d => 0.2 + d.confidence * 0.6)
      )
      .force(
        'charge',
        forceManyBody<BallSimNode>()
          .strength(d => -40 - d.linkCount * 14)
          .distanceMax(520)
      )
      .force(
        'collide',
        forceCollide<BallSimNode>()
          .radius(d => nodeRadius(d) + COLLIDE_PADDING)
          .strength(0.9)
          .iterations(2)
      )
      .force('center', forceCenter(cx, cy).strength(0.05))
      .force('x', forceX(cx).strength(0.03))
      .force('y', forceY(cy).strength(0.03))
      .alpha(1)
      .alphaDecay(0.022)
      .on('tick', onTick)

    publishSnapshot()
  }

  function toggleArticle(sectionId: number) {
    selectedProposalId.value = null
    selectedArticleId.value
      = selectedArticleId.value === sectionId ? null : sectionId
    publishSnapshot()
  }

  function toggleProposal(proposalId: number) {
    selectedArticleId.value = null
    selectedProposalId.value
      = selectedProposalId.value === proposalId ? null : proposalId
    publishSnapshot()
  }

  function clearSelection() {
    selectedArticleId.value = null
    selectedProposalId.value = null
    publishSnapshot()
  }

  function resetFilters() {
    Object.assign(filters, createDefaultFilters())
  }

  function startDrag(nodeId: string) {
    if (layoutMode.value === 'circles') return
    const node = nodeById.get(nodeId)
    if (!node || !simulation) return
    simulation.alphaTarget(0.3).restart()
    node.fx = node.x
    node.fy = node.y
  }

  function dragNode(nodeId: string, x: number, y: number) {
    if (layoutMode.value === 'circles') return
    const node = nodeById.get(nodeId)
    if (!node) return
    node.fx = x
    node.fy = y
  }

  function endDrag(nodeId: string) {
    if (layoutMode.value === 'circles') return
    const node = nodeById.get(nodeId)
    if (!node || !simulation) return
    node.fx = null
    node.fy = null
    simulation.alphaTarget(0)
  }

  watch(
    () => [
      toValue(sections),
      toValue(proposals),
      toValue(matches),
      toValue(viewportWidth),
      toValue(viewportHeight),
      layoutMode.value,
      filters.degreeFloor,
      filters.articleLinksMin,
      filters.articleLinksMax,
      filters.proposalAuthorType,
      filters.proposalLinksMin,
      filters.proposalLinksMax
    ] as const,
    () => rebuildSimulation(),
    { immediate: true }
  )

  onBeforeUnmount(() => {
    stopSimulation()
  })

  return {
    simNodes,
    simLinks,
    layoutMode,
    filters,
    linkCountBounds,
    totals,
    visible,
    hasActiveFilters,
    hasSelection,
    selectedArticleId,
    selectedProposalId,
    selectedDetail,
    neighborIds,
    dimmedOpacity: DIMMED_OPACITY,
    toggleArticle,
    toggleProposal,
    clearSelection,
    resetFilters,
    startDrag,
    dragNode,
    endDrag,
    bezierPath,
    hexagonPoints
  }
}
