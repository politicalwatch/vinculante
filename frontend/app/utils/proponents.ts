import type { Proposal } from '~/types/api'

export interface ProponentOption {
  label: string
  value: string
  count: number
}

/** `'all'` passes everything; otherwise any of the proposal's authors must match. */
export function matchesProponent(proposal: Pick<Proposal, 'authors'>, selected: string): boolean {
  return selected === 'all' || proposal.authors.includes(selected)
}

/**
 * Options for the "Proponente" filter: `Todos` plus one per distinct author.
 *
 * Which authors are listed, and their order, come from every proposal of the law,
 * so the list stays put while other filters change; `count` describes `pool`, the
 * proposals the current tab shows. A proposal with several authors counts for each.
 * Shown even with a single author, since it also tells who made the proposals;
 * `undefined` (filter hidden) only when no proposal has an author.
 */
export function buildProponentOptions(
  allProposals: Pick<Proposal, 'authors'>[],
  pool: Pick<Proposal, 'authors'>[]
): ProponentOption[] | undefined {
  const totals = countByAuthor(allProposals)
  if (totals.size === 0) return undefined

  const counts = countByAuthor(pool)
  const names = [...totals.keys()].sort(
    (a, b) => totals.get(b)! - totals.get(a)! || a.localeCompare(b, 'es')
  )
  return [
    { label: 'Todos', value: 'all', count: pool.length },
    ...names.map(name => ({ label: name, value: name, count: counts.get(name) ?? 0 }))
  ]
}

function countByAuthor(proposals: Pick<Proposal, 'authors'>[]): Map<string, number> {
  const counts = new Map<string, number>()
  for (const proposal of proposals) {
    for (const author of new Set(proposal.authors)) {
      counts.set(author, (counts.get(author) ?? 0) + 1)
    }
  }
  return counts
}
