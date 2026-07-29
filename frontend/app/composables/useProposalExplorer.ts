import type { MaybeRefOrGetter } from 'vue'
import type { Match, Proposal } from '~/types/api'
import {
  PROPOSAL_CARD_HEIGHT,
  PROPOSAL_CARD_WIDTH,
  type EditorialArticle,
  type EditorialProposal
} from '~/composables/useEditorialBoard'
import { countLinksByProposal } from '~/utils/graphFilters'
import { assignProponents, PROPONENTS } from '~/utils/mockProponents'
import { mulberry32 } from '~/utils/random'

export type ProposalGrouping = 'none' | 'linkCount'

export interface ProponentOption {
  label: string
  value: string
  count: number
}

export interface ProposalColumn {
  key: number
  label: string
  x: number
  proposals: EditorialProposal[]
}

const SURFACE_WIDTH_FACTOR = 2.4
const SCATTER_GAP_X = 56
const SCATTER_GAP_Y = 40
const COLUMN_GAP = 48
const COLUMN_PADDING_X = 24
const COLUMN_HEADER_HEIGHT = 48
const COLUMN_TOP = 16
const FALLBACK_LAYER_WIDTH = 900
const FALLBACK_LAYER_HEIGHT = 700
const LINK_COUNT_CAP = 5

const DEGREE_RANK: Record<string, number> = { alto: 3, medio: 2, bajo: 1, ninguno: 0 }

const COLUMN_LABELS: Record<number, string> = {
  0: 'Sin vinculación',
  1: '1 artículo',
  2: '2 artículos',
  3: '3 artículos',
  4: '4 artículos',
  5: '5 o más artículos'
}

function relationLabel(
  proposal: Proposal,
  linkCount: number,
  sectionIdsByProposal: Map<number, number[]>,
  articleNumberBySection: Map<number, string | null>
): string {
  if (linkCount === 0) return proposal.topic || 'sin vinculación'
  if (linkCount === 1) {
    const sectionId = sectionIdsByProposal.get(proposal.id)?.[0]
    const number = sectionId === undefined
      ? null
      : articleNumberBySection.get(sectionId)
    return number ? `vinc. con Art. ${number}` : 'vinc. con 1 artículo'
  }
  return `vinc. con ${linkCount} artículos`
}

function buildEditorialProposal(
  proposal: Proposal,
  index: number,
  linkCount: number,
  position: { x: number, y: number },
  expanded: boolean,
  height: number,
  sectionIdsByProposal: Map<number, number[]>,
  articleNumberBySection: Map<number, string | null>,
  floating: boolean
): EditorialProposal {
  const random = mulberry32(proposal.id * 40503 + 7)
  return {
    proposalId: proposal.id,
    label: `PROPUESTA #${String(proposal.id).padStart(3, '0')}`,
    relationLabel: relationLabel(
      proposal,
      linkCount,
      sectionIdsByProposal,
      articleNumberBySection
    ),
    text: proposal.text,
    linkCount,
    accentSide: index % 2 === 0 ? 'left' : 'right',
    x: position.x,
    y: position.y,
    height,
    expanded,
    floatDuration: 6 + random() * 5,
    floatDelay: -random() * 6,
    floatX: (random() - 0.5) * 20,
    floatY: (random() - 0.5) * 20,
    floating: floating && !expanded,
    stacked: false,
    opacity: 1,
    zIndex: expanded ? 300 : 1
  }
}

export function useProposalExplorer(
  proposals: MaybeRefOrGetter<Proposal[]>,
  matches: MaybeRefOrGetter<Match[]>,
  articles: MaybeRefOrGetter<EditorialArticle[]>,
  allProposals: MaybeRefOrGetter<Proposal[]> = proposals,
  layerWidth: MaybeRefOrGetter<number> = FALLBACK_LAYER_WIDTH,
  layerHeight: MaybeRefOrGetter<number> = FALLBACK_LAYER_HEIGHT
) {
  const grouping = ref<ProposalGrouping>('none')
  const proponent = ref<string>('all')
  const selectedProposalId = ref<number | null>(null)
  const expandedProposalIds = ref<Set<number>>(new Set())
  const proposalHeights = ref<Map<number, number>>(new Map())
  const expandedArticleIds = ref<Set<number>>(new Set())

  /** Assignment is derived from the full set so filters do not reshuffle organisations. */
  const proponentById = computed(() => assignProponents(toValue(allProposals)))

  const proponentOptions = computed<ProponentOption[]>(() => {
    const visibleIds = new Set(toValue(proposals).map(p => p.id))
    const counts = new Map<string, number>()
    for (const name of PROPONENTS) counts.set(name, 0)
    for (const [id, name] of proponentById.value) {
      if (!visibleIds.has(id)) continue
      counts.set(name, (counts.get(name) ?? 0) + 1)
    }
    return [
      { label: 'Todos', value: 'all', count: toValue(proposals).length },
      ...PROPONENTS.map(name => ({
        label: name,
        value: name as string,
        count: counts.get(name) ?? 0
      }))
    ]
  })

  const explorerProposals = computed(() => {
    const list = toValue(proposals)
    if (proponent.value === 'all') return list
    return list.filter(p => proponentById.value.get(p.id) === proponent.value)
  })

  const linkCounts = computed(() => countLinksByProposal(toValue(matches)))

  const sectionIdsByProposal = computed(() => {
    const map = new Map<number, number[]>()
    for (const match of toValue(matches)) {
      const list = map.get(match.proposal_id)
      if (list) list.push(match.section_id)
      else map.set(match.proposal_id, [match.section_id])
    }
    return map
  })

  const articleNumberBySection = computed(() => {
    const map = new Map<number, string | null>()
    for (const article of toValue(articles)) {
      map.set(article.sectionId, article.number)
    }
    return map
  })

  const articleById = computed(() => {
    const map = new Map<number, EditorialArticle>()
    for (const article of toValue(articles)) {
      map.set(article.sectionId, article)
    }
    return map
  })

  function proposalHeight(proposalId: number): number {
    if (!expandedProposalIds.value.has(proposalId)) return PROPOSAL_CARD_HEIGHT
    return Math.max(
      PROPOSAL_CARD_HEIGHT,
      proposalHeights.value.get(proposalId) ?? PROPOSAL_CARD_HEIGHT
    )
  }

  const idleLayout = computed(() => {
    const list = explorerProposals.value
    const viewWidth = toValue(layerWidth) || FALLBACK_LAYER_WIDTH
    const viewHeight = toValue(layerHeight) || FALLBACK_LAYER_HEIGHT

    const cellWidth = PROPOSAL_CARD_WIDTH + SCATTER_GAP_X
    const cellHeight = PROPOSAL_CARD_HEIGHT + SCATTER_GAP_Y
    const columns = Math.max(1, Math.floor((viewWidth * SURFACE_WIDTH_FACTOR) / cellWidth))
    const rows = Math.max(1, Math.ceil(list.length / columns))

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

  const columns = computed<ProposalColumn[]>(() => {
    if (grouping.value !== 'linkCount') return []

    const buckets = new Map<number, Proposal[]>()
    for (let key = 0; key <= LINK_COUNT_CAP; key++) buckets.set(key, [])

    for (const proposal of explorerProposals.value) {
      const raw = linkCounts.value.get(proposal.id) ?? 0
      const key = Math.min(raw, LINK_COUNT_CAP)
      buckets.get(key)!.push(proposal)
    }

    const result: ProposalColumn[] = []
    let columnIndex = 0

    for (let key = 0; key <= LINK_COUNT_CAP; key++) {
      const list = buckets.get(key) ?? []
      if (list.length === 0) continue

      const x = COLUMN_PADDING_X + columnIndex * (PROPOSAL_CARD_WIDTH + COLUMN_GAP)
      const cards: EditorialProposal[] = []
      let cursor = COLUMN_TOP + COLUMN_HEADER_HEIGHT

      list.forEach((proposal, index) => {
        const linkCount = linkCounts.value.get(proposal.id) ?? 0
        const expanded = expandedProposalIds.value.has(proposal.id)
        const height = proposalHeight(proposal.id)
        cards.push(
          buildEditorialProposal(
            proposal,
            index,
            linkCount,
            { x, y: cursor },
            expanded,
            height,
            sectionIdsByProposal.value,
            articleNumberBySection.value,
            false
          )
        )
        cursor += height + SCATTER_GAP_Y
      })

      result.push({
        key,
        label: COLUMN_LABELS[key] ?? `${key} artículos`,
        x,
        proposals: cards
      })
      columnIndex += 1
    }

    return result
  })

  const boardProposals = computed<EditorialProposal[]>(() => {
    if (grouping.value === 'linkCount') {
      return columns.value.flatMap(column => column.proposals)
    }

    const scatter = idleLayout.value.positions
    const counts = linkCounts.value

    return explorerProposals.value.map((proposal, index) => {
      const linkCount = counts.get(proposal.id) ?? 0
      const expanded = expandedProposalIds.value.has(proposal.id)
      return buildEditorialProposal(
        proposal,
        index,
        linkCount,
        scatter.get(proposal.id) ?? { x: SCATTER_GAP_X, y: SCATTER_GAP_Y },
        expanded,
        proposalHeight(proposal.id),
        sectionIdsByProposal.value,
        articleNumberBySection.value,
        true
      )
    })
  })

  const surfaceSize = computed(() => {
    if (grouping.value === 'linkCount') {
      const cols = columns.value
      const viewWidth = toValue(layerWidth) || FALLBACK_LAYER_WIDTH
      const viewHeight = toValue(layerHeight) || FALLBACK_LAYER_HEIGHT
      const width = cols.length === 0
        ? viewWidth
        : Math.max(
          viewWidth,
          COLUMN_PADDING_X
            + cols.length * (PROPOSAL_CARD_WIDTH + COLUMN_GAP)
            - COLUMN_GAP
            + COLUMN_PADDING_X
        )
      const height = Math.max(
        viewHeight,
        ...cols.map((column) => {
          const last = column.proposals[column.proposals.length - 1]
          return last ? last.y + last.height + SCATTER_GAP_Y : COLUMN_TOP + COLUMN_HEADER_HEIGHT
        })
      )
      return { width, height }
    }
    return {
      width: idleLayout.value.width,
      height: idleLayout.value.height
    }
  })

  const hasSelection = computed(() => selectedProposalId.value !== null)

  const selectedProposal = computed(() => {
    if (selectedProposalId.value === null) return null
    return boardProposals.value.find(p => p.proposalId === selectedProposalId.value) ?? null
  })

  const linkedArticles = computed<EditorialArticle[]>(() => {
    if (selectedProposalId.value === null) return []
    const proposalId = selectedProposalId.value
    const related = toValue(matches)
      .filter(m => m.proposal_id === proposalId)
      .sort((a, b) => {
        const degree
          = (DEGREE_RANK[b.degree ?? 'ninguno'] ?? 0) - (DEGREE_RANK[a.degree ?? 'ninguno'] ?? 0)
        if (degree !== 0) return degree
        return (b.confidence ?? 0) - (a.confidence ?? 0)
      })

    const seen = new Set<number>()
    const result: EditorialArticle[] = []
    for (const match of related) {
      if (seen.has(match.section_id)) continue
      seen.add(match.section_id)
      const article = articleById.value.get(match.section_id)
      if (article) result.push(article)
    }
    return result
  })

  const visibleCount = computed(() => explorerProposals.value.length)

  function selectProposal(proposalId: number) {
    const linkCount = linkCounts.value.get(proposalId) ?? 0
    if (linkCount === 0) {
      toggleProposalExpanded(proposalId)
      return
    }
    selectedProposalId.value
      = selectedProposalId.value === proposalId ? null : proposalId
  }

  function clearSelection() {
    selectedProposalId.value = null
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

  function isArticleExpanded(sectionId: number): boolean {
    return expandedArticleIds.value.has(sectionId)
  }

  function toggleArticleExpanded(sectionId: number) {
    const next = new Set(expandedArticleIds.value)
    if (next.has(sectionId)) next.delete(sectionId)
    else next.add(sectionId)
    expandedArticleIds.value = next
  }

  watch(
    () => explorerProposals.value,
    (list) => {
      if (selectedProposalId.value === null) return
      if (!list.some(p => p.id === selectedProposalId.value)) {
        selectedProposalId.value = null
      }
    }
  )

  return {
    grouping,
    proponent,
    proponentOptions,
    selectedProposalId,
    hasSelection,
    selectedProposal,
    linkedArticles,
    boardProposals,
    columns,
    surfaceSize,
    visibleCount,
    selectProposal,
    clearSelection,
    toggleProposalExpanded,
    setProposalHeight,
    isArticleExpanded,
    toggleArticleExpanded
  }
}
