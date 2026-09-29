import { describe, it, expect } from 'vitest'
import type { Match, MatchDegree, Proposal, Section } from '../../../app/types/api'
import {
  applyGraphFilters,
  clampLinkRanges,
  countLinksByProposal,
  countLinksBySection,
  createDefaultFilters,
  inLinkRange,
  matchesDegreeFloor,
  type GraphFilters
} from '../../../app/utils/graphFilters'

function section(id: number, isMatchable = true): Section {
  return {
    id,
    text: `artículo ${id}`,
    text_markdown: null,
    clear_language: null,
    page_number: null,
    section_type: null,
    section_number: null,
    parent_id: null,
    target_id: 1,
    is_matchable: isMatchable
  }
}

function proposal(id: number, authorType: string | null = 'citizen'): Proposal {
  return {
    id,
    text: `propuesta ${id}`,
    authors: [],
    author_type: authorType,
    reference: null,
    topic: null,
    subtopic: null,
    source_file: null
  }
}

let nextMatchId = 1
function match(proposalId: number, sectionId: number, degree: MatchDegree | null): Match {
  return {
    id: nextMatchId++,
    proposal_id: proposalId,
    section_id: sectionId,
    degree,
    explanation: null,
    confidence: null,
    status: 'pending',
    section_spans: null,
    proposal: proposal(proposalId)
  }
}

function filters(overrides: Partial<GraphFilters> = {}): GraphFilters {
  return { ...createDefaultFilters(), ...overrides }
}

describe('matchesDegreeFloor', () => {
  it('accepts degrees at or above the floor', () => {
    expect(matchesDegreeFloor('alto', 'medio')).toBe(true)
    expect(matchesDegreeFloor('medio', 'medio')).toBe(true)
    expect(matchesDegreeFloor('bajo', 'medio')).toBe(false)
    expect(matchesDegreeFloor('bajo', 'bajo')).toBe(true)
  })

  it('never accepts ninguno or a missing degree', () => {
    expect(matchesDegreeFloor('ninguno', 'bajo')).toBe(false)
    expect(matchesDegreeFloor(null, 'bajo')).toBe(false)
  })
})

describe('inLinkRange', () => {
  it('is inclusive at both ends', () => {
    expect(inLinkRange(2, 2, 4)).toBe(true)
    expect(inLinkRange(4, 2, 4)).toBe(true)
    expect(inLinkRange(1, 2, 4)).toBe(false)
    expect(inLinkRange(5, 2, 4)).toBe(false)
  })

  it('treats a null max as no upper bound', () => {
    expect(inLinkRange(1000, 0, null)).toBe(true)
  })
})

describe('countLinks', () => {
  const matches = [match(1, 10, 'alto'), match(1, 11, 'medio'), match(2, 10, 'bajo')]

  it('counts matches per section', () => {
    expect(countLinksBySection(matches)).toEqual(new Map([[10, 2], [11, 1]]))
  })

  it('counts matches per proposal', () => {
    expect(countLinksByProposal(matches)).toEqual(new Map([[1, 2], [2, 1]]))
  })
})

describe('clampLinkRanges', () => {
  const bounds = { articleMax: 3, proposalMax: 2 }

  it('pulls minimums above the bound down to it and drops maxes past it', () => {
    const clamped = clampLinkRanges(
      filters({ articleLinksMin: 5, articleLinksMax: 8, proposalLinksMin: 4, proposalLinksMax: 2 }),
      bounds
    )

    expect(clamped).toMatchObject({
      articleLinksMin: 3,
      articleLinksMax: null,
      proposalLinksMin: 2,
      proposalLinksMax: null
    })
  })

  it('leaves ranges inside the bounds untouched', () => {
    const inside = filters({ degreeFloor: 'alto', articleLinksMin: 1, articleLinksMax: 2, proposalLinksMin: 1 })
    expect(clampLinkRanges(inside, bounds)).toEqual(inside)
  })
})

describe('createDefaultFilters', () => {
  it('starts at the medio floor with no link or author limits', () => {
    expect(createDefaultFilters()).toEqual({
      degreeFloor: 'medio',
      articleLinksMin: 0,
      articleLinksMax: null,
      proposalAuthorType: 'all',
      proposalLinksMin: 0,
      proposalLinksMax: null
    })
  })

  it('returns a fresh object each time', () => {
    expect(createDefaultFilters()).not.toBe(createDefaultFilters())
  })
})

describe('applyGraphFilters', () => {
  // Sections 10, 11, 12 are matchable; 13 (a preamble) is not.
  // Proposals 1, 2 are citizen, 3 is academia.
  const sections = [section(10), section(11), section(12), section(13, false)]
  const proposals = [proposal(1), proposal(2), proposal(3, 'academia')]
  const matches = [
    match(1, 10, 'alto'),
    match(1, 11, 'medio'),
    match(2, 10, 'medio'),
    match(3, 12, 'bajo'),
    match(3, 11, 'ninguno')
  ]

  it('keeps only matchable sections', () => {
    const result = applyGraphFilters(sections, proposals, matches, filters())

    expect(result.sections.map(s => s.id)).toEqual([10, 11, 12])
    expect(result.totals.articles).toBe(3)
  })

  it('drops matches below the degree floor and counts totals after it', () => {
    const result = applyGraphFilters(sections, proposals, matches, filters({ degreeFloor: 'medio' }))

    expect(result.matches.map(m => m.degree).sort()).toEqual(['alto', 'medio', 'medio'])
    expect(result.totals).toEqual({ articles: 3, proposals: 3, matches: 3 })
  })

  it('derives link-count bounds from the degree-filtered matches', () => {
    expect(applyGraphFilters(sections, proposals, matches, filters({ degreeFloor: 'medio' })).linkCountBounds)
      .toEqual({ articleMax: 2, proposalMax: 2 })
    expect(applyGraphFilters(sections, proposals, matches, filters({ degreeFloor: 'alto' })).linkCountBounds)
      .toEqual({ articleMax: 1, proposalMax: 1 })
  })

  it('filters articles by their link count', () => {
    const result = applyGraphFilters(sections, proposals, matches, filters({ articleLinksMin: 2 }))

    expect(result.sections.map(s => s.id)).toEqual([10])
    // Matches to hidden articles disappear too
    expect(result.matches.every(m => m.section_id === 10)).toBe(true)
    expect(result.visible).toEqual({ articles: 1, proposals: 3, matches: 2 })
  })

  it('filters proposals by link count, including those with no links', () => {
    const unlinked = applyGraphFilters(sections, proposals, matches, filters({ proposalLinksMax: 0 }))
    expect(unlinked.proposals.map(p => p.id)).toEqual([3])
    expect(unlinked.matches).toEqual([])

    const linked = applyGraphFilters(sections, proposals, matches, filters({ proposalLinksMin: 1 }))
    expect(linked.proposals.map(p => p.id)).toEqual([1, 2])
  })

  it('filters proposals by author type', () => {
    const result = applyGraphFilters(
      sections, proposals, matches, filters({ degreeFloor: 'bajo', proposalAuthorType: 'academia' })
    )

    expect(result.proposals.map(p => p.id)).toEqual([3])
    expect(result.matches.map(m => m.degree)).toEqual(['bajo'])
    expect(result.totals.proposals).toBe(3)
  })

  it('keeps totals independent of the link and author filters', () => {
    const result = applyGraphFilters(
      sections, proposals, matches, filters({ articleLinksMin: 5, proposalAuthorType: 'academia' })
    )

    expect(result.visible).toEqual({ articles: 0, proposals: 1, matches: 0 })
    expect(result.totals).toEqual({ articles: 3, proposals: 3, matches: 3 })
  })
})
