import type { MaybeRefOrGetter } from 'vue'
import type { Match, Proposal, Section } from '~/types/api'
import {
  createDefaultFilters,
  type GraphFilters,
  type GraphTotalCounts,
  type GraphVisibleCounts,
  type LinkCountBounds
} from '~/composables/useExperimentalGraph'
import { applyGraphFilters, countLinksByProposal } from '~/utils/graphFilters'
import { assignProponents, PROPONENTS, type ProponentOption } from '~/utils/mockProponents'
import { mulberry32 } from '~/utils/random'

export type BoardView = 'articles' | 'proposals'

/** Minimap geometry — every value is tunable from here. */
export const MINIMAP_CONFIG = {
  /** Width of an article with zero vinculaciones. */
  baseWidth: 12,
  /** The most-linked article is this many times wider. */
  maxWidthFactor: 3,
  /** Height of an article shorter than 100 words. */
  baseHeight: 12,
  /** Added height per 100 words of article text. */
  pxPer100Words: 4,
  maxHeight: 48,
  gap: 4
} as const

export const ARTICLE_COLUMN_WIDTH = 580
export const PROPOSAL_CARD_WIDTH = 364
export const PROPOSAL_CARD_HEIGHT = 113

const STACK_OFFSET_X = 32
const STACK_TOP = 8
const STACK_GAP = 12
const SURFACE_WIDTH_FACTOR = 2.4
const SCATTER_GAP_X = 56
const SCATTER_GAP_Y = 40
const FALLBACK_LAYER_WIDTH = 900
const FALLBACK_LAYER_HEIGHT = 700
const TITLE_MAX_LENGTH = 90
const DIMMED_ARTICLE_OPACITY = 0.25

const DEGREE_RANK: Record<string, number> = { alto: 3, medio: 2, bajo: 1, ninguno: 0 }

export interface EditorialArticle {
  sectionId: number
  /** Raw `section_number`, e.g. "1". */
  number: string | null
  /** Zero-padded display label, e.g. "ARTÍCULO 01". */
  label: string
  title: string
  body: string
  fullText: string
  linkCount: number
  wordCount: number
  /** 0–1 share of the document's busiest article. */
  linkRatio: number
  minimapWidth: number
  minimapHeight: number
}

export interface EditorialProposal {
  proposalId: number
  label: string
  relationLabel: string
  text: string
  linkCount: number
  accentSide: 'left' | 'right'
  x: number
  y: number
  /** Measured height once expanded, collapsed height otherwise. */
  height: number
  expanded: boolean
  /** Idle float animation parameters, stable per proposal. */
  floatDuration: number
  floatDelay: number
  floatX: number
  floatY: number
  floating: boolean
  stacked: boolean
  opacity: number
  zIndex: number
}

export interface StackConnectors {
  /** Vertical bracket spanning the stack. */
  spine: string
  /** Short horizontal tick from the spine into each stacked card. */
  ticks: Array<{ proposalId: number, path: string }>
  width: number
  height: number
}

function stripMarkdown(value: string): string {
  return value
    .replace(/^#{1,6}\s+/, '')
    .replace(/\*\*(.+?)\*\*/g, '$1')
    .replace(/[*_`]/g, '')
    .trim()
}

function normalizeForCompare(value: string): string {
  return stripMarkdown(value).toLowerCase().replace(/\s+/g, ' ').replace(/[.:;]$/, '')
}

function firstSentence(value: string, max: number): string {
  const trimmed = value.trim()
  const stop = trimmed.search(/[.;:]\s/)
  const candidate = stop > 0 ? trimmed.slice(0, stop) : trimmed
  if (candidate.length <= max) return candidate
  return `${candidate.slice(0, max).trimEnd()}…`
}

/**
 * Sections bundle the article rubric and its body: `text_markdown` opens with a
 * `## <rubric>` heading which is also the first paragraph of `text`. Split them so
 * the card can show a title above the body.
 */
function deriveTitleAndBody(section: Section): { title: string, body: string } {
  const raw = section.clear_language || section.text
  const paragraphs = raw
    .split(/\n{2,}/)
    .map(p => p.trim())
    .filter(Boolean)

  const heading = section.text_markdown?.match(/^\s*#{1,6}\s+(.+?)\s*$/m)?.[1]
  const candidate = heading ? stripMarkdown(heading) : (paragraphs[0] ?? '')

  if (candidate && candidate.length <= TITLE_MAX_LENGTH) {
    const key = normalizeForCompare(candidate)
    const body = paragraphs.filter(p => normalizeForCompare(p) !== key)
    return { title: candidate, body: body.join('\n\n') }
  }

  return {
    title: firstSentence(paragraphs[0] ?? '', TITLE_MAX_LENGTH),
    body: paragraphs.join('\n\n')
  }
}

function countWords(value: string): number {
  const trimmed = value.trim()
  if (!trimmed) return 0
  return trimmed.split(/\s+/).length
}

function articleLabel(sectionNumber: string | null): string {
  if (!sectionNumber) return 'ARTÍCULO'
  const numeric = Number(sectionNumber)
  if (Number.isFinite(numeric)) {
    return `ARTÍCULO ${String(numeric).padStart(2, '0')}`
  }
  return `ARTÍCULO ${sectionNumber.toUpperCase()}`
}

function minimapWidth(linkCount: number, maxLinkCount: number): number {
  const { baseWidth, maxWidthFactor } = MINIMAP_CONFIG
  if (maxLinkCount <= 0) return baseWidth
  const ratio = Math.min(1, linkCount / maxLinkCount)
  return Math.round(baseWidth + ratio * baseWidth * (maxWidthFactor - 1))
}

function minimapHeight(wordCount: number): number {
  const { baseHeight, pxPer100Words, maxHeight } = MINIMAP_CONFIG
  const extra = Math.floor(wordCount / 100) * pxPer100Words
  return Math.min(maxHeight, baseHeight + extra)
}

export function useEditorialBoard(
  sections: MaybeRefOrGetter<Section[] | null | undefined>,
  proposals: MaybeRefOrGetter<Proposal[] | null | undefined>,
  matches: MaybeRefOrGetter<Match[] | null | undefined>,
  layerWidth: MaybeRefOrGetter<number> = FALLBACK_LAYER_WIDTH,
  layerHeight: MaybeRefOrGetter<number> = FALLBACK_LAYER_HEIGHT
) {
  const filters = reactive<GraphFilters>(createDefaultFilters())
  const selectedArticleId = ref<number | null>(null)
  const expandedArticleIds = ref<Set<number>>(new Set())
  const expandedProposalIds = ref<Set<number>>(new Set())
  /**
   * Expanded cards grow to fit their text, so their height is reported back by the
   * card instead of estimated here — the stack below has to shift by the real amount.
   */
  const proposalHeights = ref<Map<number, number>>(new Map())

  const view = ref<BoardView>('articles')
  /** Organisation filter, shared by Vinculaciones and Propuestas. `'all'` shows every proponent. */
  const proponent = ref('all')

  /**
   * The proposal article-count range is a Propuestas control. Vinculaciones
   * ignores it so a hidden slider cannot change which cards are on the board.
   */
  const appliedFilters = computed<GraphFilters>(() => {
    if (view.value === 'proposals') return filters
    return {
      ...filters,
      proposalLinksMin: 0,
      proposalLinksMax: null
    }
  })

  const filtered = computed(() =>
    applyGraphFilters(
      toValue(sections) ?? [],
      toValue(proposals) ?? [],
      toValue(matches) ?? [],
      appliedFilters.value
    )
  )

  /** Stable across filters so the same proposal keeps its organisation. */
  const proponentById = computed(() => assignProponents(toValue(proposals) ?? []))

  function matchesProponent(proposalId: number): boolean {
    if (proponent.value === 'all') return true
    return proponentById.value.get(proposalId) === proponent.value
  }

  const scopedProposals = computed(() =>
    filtered.value.proposals.filter(p => matchesProponent(p.id))
  )
  const scopedMatches = computed(() =>
    filtered.value.matches.filter(m => matchesProponent(m.proposal_id))
  )

  const filteredProposals = computed(() => scopedProposals.value)
  const filteredMatches = computed(() => scopedMatches.value)

  /**
   * Vinculaciones only shows proposals that survive the degree floor with at least
   * one match. The Propuestas tab keeps `filteredProposals`, including the ones
   * with no vinculación.
   */
  const linkedProposals = computed(() => {
    const counts = countLinksByProposal(scopedMatches.value)
    return scopedProposals.value.filter(p => (counts.get(p.id) ?? 0) > 0)
  })

  /**
   * Counts in the dropdown describe the current tab before the proponent filter,
   * so picking an organisation does not shrink the numbers of the others.
   */
  const proponentOptions = computed<ProponentOption[]>(() => {
    const linkCounts = countLinksByProposal(filtered.value.matches)
    const pool = view.value === 'proposals'
      ? filtered.value.proposals
      : filtered.value.proposals.filter(proposal => (linkCounts.get(proposal.id) ?? 0) > 0)
    const visibleIds = new Set(pool.map(p => p.id))
    const counts = new Map<string, number>()
    for (const name of PROPONENTS) counts.set(name, 0)
    for (const [id, name] of proponentById.value) {
      if (!visibleIds.has(id)) continue
      counts.set(name, (counts.get(name) ?? 0) + 1)
    }
    return [
      { label: 'Todos', value: 'all', count: pool.length },
      ...PROPONENTS.map(name => ({
        label: name,
        value: name,
        count: counts.get(name) ?? 0
      }))
    ]
  })

  const linkCountBounds = computed<LinkCountBounds>(() => filtered.value.linkCountBounds)
  const totals = computed<GraphTotalCounts>(() => filtered.value.totals)
  const visible = computed<GraphVisibleCounts>(() => ({
    ...filtered.value.visible,
    proposals: scopedProposals.value.length,
    matches: scopedMatches.value.length
  }))

  const hasActiveFilters = computed(() => {
    const defaults = createDefaultFilters()
    return (
      filters.degreeFloor !== defaults.degreeFloor
      || filters.articleLinksMin !== defaults.articleLinksMin
      || filters.articleLinksMax !== defaults.articleLinksMax
      || filters.proposalAuthorType !== defaults.proposalAuthorType
      || proponent.value !== 'all'
      || (
        view.value === 'proposals'
        && (
          filters.proposalLinksMin !== defaults.proposalLinksMin
          || filters.proposalLinksMax !== defaults.proposalLinksMax
        )
      )
    )
  })

  /** Matches of the current filter set, grouped both ways. */
  const matchesBySection = computed(() => {
    const map = new Map<number, Match[]>()
    for (const match of scopedMatches.value) {
      const list = map.get(match.section_id)
      if (list) list.push(match)
      else map.set(match.section_id, [match])
    }
    return map
  })

  const articleNumberBySection = computed(() => {
    const map = new Map<number, string | null>()
    for (const section of filtered.value.sections) {
      map.set(section.id, section.section_number)
    }
    return map
  })

  const sectionIdsByProposal = computed(() => {
    const map = new Map<number, number[]>()
    for (const match of scopedMatches.value) {
      const list = map.get(match.proposal_id)
      if (list) list.push(match.section_id)
      else map.set(match.proposal_id, [match.section_id])
    }
    return map
  })

  const articles = computed<EditorialArticle[]>(() => {
    const counts = matchesBySection.value
    const maxLinkCount = filtered.value.sections.reduce(
      (max, s) => Math.max(max, counts.get(s.id)?.length ?? 0),
      0
    )

    return filtered.value.sections.map((section) => {
      const linkCount = counts.get(section.id)?.length ?? 0
      const { title, body } = deriveTitleAndBody(section)
      const fullText = section.clear_language || section.text
      const wordCount = countWords(fullText)

      return {
        sectionId: section.id,
        number: section.section_number,
        label: articleLabel(section.section_number),
        title,
        body,
        fullText,
        linkCount,
        wordCount,
        linkRatio: maxLinkCount > 0 ? linkCount / maxLinkCount : 0,
        minimapWidth: minimapWidth(linkCount, maxLinkCount),
        minimapHeight: minimapHeight(wordCount)
      }
    })
  })

  const relatedProposalIds = computed<number[]>(() => {
    if (selectedArticleId.value === null) return []
    const list = matchesBySection.value.get(selectedArticleId.value) ?? []
    return [...list]
      .sort((a, b) => {
        const degree
          = (DEGREE_RANK[b.degree ?? 'ninguno'] ?? 0) - (DEGREE_RANK[a.degree ?? 'ninguno'] ?? 0)
        if (degree !== 0) return degree
        return (b.confidence ?? 0) - (a.confidence ?? 0)
      })
      .map(m => m.proposal_id)
  })

  const relatedProposalIdSet = computed(() => new Set(relatedProposalIds.value))

  const hasSelection = computed(() => selectedArticleId.value !== null)

  function proposalHeight(proposalId: number): number {
    if (!expandedProposalIds.value.has(proposalId)) return PROPOSAL_CARD_HEIGHT
    return Math.max(
      PROPOSAL_CARD_HEIGHT,
      proposalHeights.value.get(proposalId) ?? PROPOSAL_CARD_HEIGHT
    )
  }

  /**
   * Idle scatter across a canvas wider and taller than the viewport, so only a
   * handful of cards are ever in view.
   *
   * Cards are placed on a jittered, row-staggered grid rather than relaxed with a
   * force simulation: `forceCollide` is circular, so at 364x113 it cannot separate
   * these cards horizontally without wasting most of the vertical space. A grid
   * guarantees no overlap, and the jitter plus stagger keeps it from reading as a grid.
   */
  const idleLayout = computed(() => {
    const list = linkedProposals.value
    const viewWidth = toValue(layerWidth) || FALLBACK_LAYER_WIDTH
    const viewHeight = toValue(layerHeight) || FALLBACK_LAYER_HEIGHT

    const cellWidth = PROPOSAL_CARD_WIDTH + SCATTER_GAP_X
    const cellHeight = PROPOSAL_CARD_HEIGHT + SCATTER_GAP_Y
    const columns = Math.max(1, Math.floor((viewWidth * SURFACE_WIDTH_FACTOR) / cellWidth))
    const rows = Math.max(1, Math.ceil(list.length / columns))

    /** Deterministic shuffle so neighbouring ids don't land side by side. */
    const order = list
      .map((proposal, index) => ({ index, sort: mulberry32(proposal.id * 2654435761)() }))
      .sort((a, b) => a.sort - b.sort)

    const positions = new Map<number, { x: number, y: number }>()

    order.forEach(({ index }, slot) => {
      const proposal = list[index]
      if (!proposal) return
      const column = slot % columns
      const row = Math.floor(slot / columns)
      const random = mulberry32(proposal.id * 97 + 13)
      const stagger = row % 2 === 1 ? cellWidth / 2 : 0

      positions.set(proposal.id, {
        x: Math.round(
          column * cellWidth + stagger + SCATTER_GAP_X / 2 + (random() - 0.5) * SCATTER_GAP_X * 0.6
        ),
        y: Math.round(
          row * cellHeight + SCATTER_GAP_Y / 2 + (random() - 0.5) * SCATTER_GAP_Y * 0.6
        )
      })
    })

    return {
      positions,
      width: Math.max(viewWidth, Math.round(columns * cellWidth + cellWidth / 2 + SCATTER_GAP_X)),
      height: Math.max(viewHeight, Math.round(rows * cellHeight + SCATTER_GAP_Y))
    }
  })

  const surfaceSize = computed(() => ({
    width: idleLayout.value.width,
    height: idleLayout.value.height
  }))

  const stackLayout = computed(() => {
    const positions = new Map<number, { x: number, y: number, height: number }>()
    let cursor = STACK_TOP
    for (const proposalId of relatedProposalIds.value) {
      const height = proposalHeight(proposalId)
      positions.set(proposalId, { x: STACK_OFFSET_X, y: cursor, height })
      cursor += height + STACK_GAP
    }
    return { positions, height: cursor - STACK_GAP + STACK_TOP }
  })

  const stackHeight = computed(() => stackLayout.value.height)

  function relationLabel(proposal: Proposal, linkCount: number): string {
    if (selectedArticleId.value !== null && relatedProposalIdSet.value.has(proposal.id)) {
      const number = articleNumberBySection.value.get(selectedArticleId.value)
      return number ? `vinc. con Art. ${number}` : 'vinculada'
    }
    if (linkCount === 0) return proposal.topic || 'sin vinculación'
    if (linkCount === 1) {
      const sectionId = sectionIdsByProposal.value.get(proposal.id)?.[0]
      const number = sectionId === undefined
        ? null
        : articleNumberBySection.value.get(sectionId)
      return number ? `vinc. con Art. ${number}` : 'vinc. con 1 artículo'
    }
    return `vinc. con ${linkCount} artículos`
  }

  const boardProposals = computed<EditorialProposal[]>(() => {
    const counts = countLinksByProposal(scopedMatches.value)
    const scatter = idleLayout.value.positions
    const stack = stackLayout.value.positions
    const focused = selectedArticleId.value !== null

    return linkedProposals.value.map((proposal, index) => {
      const random = mulberry32(proposal.id * 40503 + 7)
      const isRelated = relatedProposalIdSet.value.has(proposal.id)
      const stacked = focused && isRelated
      const position
        = (stacked ? stack.get(proposal.id) : scatter.get(proposal.id))
          ?? { x: SCATTER_GAP_X, y: SCATTER_GAP_Y }
      const stackIndex = relatedProposalIds.value.indexOf(proposal.id)
      const expanded = expandedProposalIds.value.has(proposal.id)

      return {
        proposalId: proposal.id,
        label: `PROPUESTA #${String(proposal.id).padStart(3, '0')}`,
        relationLabel: relationLabel(proposal, counts.get(proposal.id) ?? 0),
        text: proposal.text,
        linkCount: counts.get(proposal.id) ?? 0,
        accentSide: index % 2 === 0 ? 'left' : 'right',
        x: position.x,
        y: position.y,
        height: proposalHeight(proposal.id),
        expanded,
        floatDuration: 6 + random() * 5,
        floatDelay: -random() * 6,
        floatX: (random() - 0.5) * 20,
        floatY: (random() - 0.5) * 20,
        floating: !focused && !expanded,
        stacked,
        opacity: focused && !isRelated ? 0 : 1,
        zIndex: expanded ? 300 : stacked ? 200 - stackIndex : 1
      }
    })
  })

  /**
   * A bracket tying the stack to the selected article. Drawn as a spine plus ticks
   * rather than one curve per proposal: over a stack of 30+ cards, curves fanning
   * from a single origin degenerate into a bundle of near-vertical lines.
   */
  const stackConnectors = computed<StackConnectors | null>(() => {
    if (selectedArticleId.value === null) return null
    const ids = relatedProposalIds.value
    if (ids.length === 0) return null

    const spineX = STACK_OFFSET_X / 2
    const stack = stackLayout.value.positions
    const centerY = (proposalId: number) => {
      const slot = stack.get(proposalId)
      if (!slot) return STACK_TOP + PROPOSAL_CARD_HEIGHT / 2
      return slot.y + slot.height / 2
    }

    const firstY = centerY(ids[0]!)
    const lastY = centerY(ids[ids.length - 1]!)

    return {
      spine: `M ${spineX} ${firstY} L ${spineX} ${lastY}`,
      ticks: ids.map(proposalId => ({
        proposalId,
        path: `M ${spineX} ${centerY(proposalId)} L ${STACK_OFFSET_X} ${centerY(proposalId)}`
      })),
      width: STACK_OFFSET_X,
      height: stackLayout.value.height
    }
  })

  function selectArticle(sectionId: number) {
    selectedArticleId.value = selectedArticleId.value === sectionId ? null : sectionId
  }

  function clearSelection() {
    selectedArticleId.value = null
  }

  function isExpanded(sectionId: number): boolean {
    return expandedArticleIds.value.has(sectionId)
  }

  function toggleExpanded(sectionId: number) {
    const next = new Set(expandedArticleIds.value)
    if (next.has(sectionId)) next.delete(sectionId)
    else next.add(sectionId)
    expandedArticleIds.value = next
  }

  function toggleProposalExpanded(proposalId: number) {
    const next = new Set(expandedProposalIds.value)
    if (next.has(proposalId)) next.delete(proposalId)
    else next.add(proposalId)
    expandedProposalIds.value = next
  }

  function setProposalHeight(proposalId: number, height: number) {
    const rounded = Math.round(height)
    if (proposalHeights.value.get(proposalId) === rounded) return
    const next = new Map(proposalHeights.value)
    next.set(proposalId, rounded)
    proposalHeights.value = next
  }

  function articleOpacity(sectionId: number): number {
    if (selectedArticleId.value === null) return 1
    return selectedArticleId.value === sectionId ? 1 : DIMMED_ARTICLE_OPACITY
  }

  function resetFilters() {
    Object.assign(filters, createDefaultFilters())
    proponent.value = 'all'
  }

  /** Drop a selection that the filters just removed from the board. */
  watch(
    () => filtered.value.sections,
    (list) => {
      if (selectedArticleId.value === null) return
      if (!list.some(s => s.id === selectedArticleId.value)) {
        selectedArticleId.value = null
      }
    }
  )

  return {
    filters,
    view,
    proponent,
    proponentOptions,
    linkCountBounds,
    totals,
    visible,
    hasActiveFilters,
    articles,
    proposals: boardProposals,
    filteredProposals,
    filteredMatches,
    stackConnectors,
    surfaceSize,
    stackHeight,
    selectedArticleId,
    hasSelection,
    relatedProposalIds,
    selectArticle,
    clearSelection,
    isExpanded,
    toggleExpanded,
    toggleProposalExpanded,
    setProposalHeight,
    articleOpacity,
    resetFilters
  }
}
