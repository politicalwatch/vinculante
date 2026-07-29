import type { Match, MatchDegree, Proposal, Section } from '~/types/api'
import type {
  DegreeFloor,
  GraphFilters,
  GraphTotalCounts,
  GraphVisibleCounts,
  LinkCountBounds
} from '~/composables/useExperimentalGraph'

const DEGREE_RANK: Record<string, number> = {
  alto: 3,
  medio: 2,
  bajo: 1,
  ninguno: 0
}

export function matchesDegreeFloor(
  degree: MatchDegree | null,
  floor: DegreeFloor
): boolean {
  if (!degree || degree === 'ninguno') return false
  return (DEGREE_RANK[degree] ?? 0) >= (DEGREE_RANK[floor] ?? 0)
}

export function inLinkRange(count: number, min: number, max: number | null): boolean {
  if (count < min) return false
  if (max !== null && count > max) return false
  return true
}

export function countLinksBySection(matches: Match[]): Map<number, number> {
  const counts = new Map<number, number>()
  for (const match of matches) {
    counts.set(match.section_id, (counts.get(match.section_id) ?? 0) + 1)
  }
  return counts
}

export function countLinksByProposal(matches: Match[]): Map<number, number> {
  const counts = new Map<number, number>()
  for (const match of matches) {
    counts.set(match.proposal_id, (counts.get(match.proposal_id) ?? 0) + 1)
  }
  return counts
}

export interface FilteredGraph {
  sections: Section[]
  proposals: Proposal[]
  matches: Match[]
  linkCountBounds: LinkCountBounds
  totals: GraphTotalCounts
  visible: GraphVisibleCounts
}

/**
 * Applies the shared experimental filters. Link-count bounds are derived from the
 * degree-filtered matches so the sliders always describe the current degree floor.
 */
export function applyGraphFilters(
  sections: Section[],
  proposals: Proposal[],
  matches: Match[],
  filters: GraphFilters
): FilteredGraph {
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
