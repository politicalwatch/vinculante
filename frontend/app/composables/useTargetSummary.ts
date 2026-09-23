import type { Section, TargetDocument } from '~/types/api'
import type { SummaryBlocks, SummaryHighlight } from '~/utils/summaryMarkdown'
import { parseHighlights, parseSummary } from '~/utils/summaryMarkdown'

/** Section types that open a new group in the document outline. */
const HEADING_TYPES = new Set(['titulo', 'capitulo', 'libro', 'parte'])

const ARTICLE_NUMBER_RE = /Art[íi]culo\s+([\dIVXLC]+)/i
const ARTICLE_PREFIX_RE = /^Art[íi]culo\s+[\dIVXLC]+\s*[.:-]?\s*/i
const PAGE_SUFFIX_RE = /\s*\(p\.\s*\d+\)\s*$/

export interface CoverageStat {
  pct: number
  sectionsMatched: number
  sectionsTotal: number
  proposalsIncorporated: number
  proposalsTotal: number
  alto: number
  medio: number
}

export interface LinkageBarItem {
  sectionId: number
  /** Short axis label, e.g. `Art. 4`. */
  label: string
  /** Heading without the `Artículo N.` prefix. */
  title: string
  articleNumber: string | null
  alto: number
  medio: number
  total: number
}

export interface LinkageGroup {
  key: string
  /** e.g. `TÍTULO I`. */
  label: string
  subtitle: string | null
  items: LinkageBarItem[]
}

export interface OrphanSection {
  sectionId: number
  label: string
  title: string
}

export interface ResolvedHighlight extends SummaryHighlight {
  /** e.g. `ART. 4 · TÍTULO I`, falling back to the raw reference. */
  shortRef: string
}

function firstLine(text: string | null | undefined): string {
  return (text ?? '').split('\n').map(line => line.trim()).find(Boolean) ?? ''
}

/** The extractor leaves runs of whitespace inside headings ("Artículo  5."). */
function collapseSpaces(text: string): string {
  return text.replace(/\s+/g, ' ').trim()
}

function groupLabelOf(section: Section): { label: string, subtitle: string | null } {
  const heading = collapseSpaces(firstLine(section.text))
  const [head, ...rest] = heading.split(':')
  const tail = rest.join(':').trim()
  const inlineSubtitle = tail || null
  const blockSubtitle = collapseSpaces(
    (section.text ?? '').split('\n').map(line => line.trim()).filter(Boolean)[1] ?? ''
  )
  return {
    label: (head ?? heading).toUpperCase(),
    subtitle: inlineSubtitle ?? (blockSubtitle || null)
  }
}

function articleNumberOf(section: Section): string | null {
  if (section.section_number && /^[\dIVXLC]+$/i.test(section.section_number)) {
    return section.section_number
  }
  return ARTICLE_NUMBER_RE.exec(section.text ?? '')?.[1] ?? null
}

function articleTitleOf(section: Section): string {
  const heading = collapseSpaces(firstLine(section.text))
  return heading.replace(ARTICLE_PREFIX_RE, '').replace(/\.$/, '') || heading
}

/**
 * Builds the outline used by the linkage chart. `parent_id` is never populated
 * by the extractor, so grouping is derived from document order: every matchable
 * section belongs to the heading that precedes it.
 */
function buildGroups(
  sections: Section[],
  counts: Map<number, { alto: number, medio: number }>
): LinkageGroup[] {
  const groups: LinkageGroup[] = []
  const leading: LinkageBarItem[] = []

  for (const section of sections) {
    if (HEADING_TYPES.has(section.section_type ?? '')) {
      const { label, subtitle } = groupLabelOf(section)
      groups.push({ key: `section-${section.id}`, label, subtitle, items: [] })
      continue
    }
    if (!section.is_matchable) continue

    const count = counts.get(section.id) ?? { alto: 0, medio: 0 }
    const articleNumber = articleNumberOf(section)
    const item: LinkageBarItem = {
      sectionId: section.id,
      label: articleNumber ? `Art. ${articleNumber}` : collapseSpaces(firstLine(section.text)).slice(0, 12),
      title: articleTitleOf(section),
      articleNumber,
      alto: count.alto,
      medio: count.medio,
      total: count.alto + count.medio
    }

    const current = groups.at(-1)
    if (current) current.items.push(item)
    else leading.push(item)
  }

  if (leading.length > 0) {
    // The extractor emits "TÍTULO PRELIMINAR" after the articles it covers, so
    // an empty first heading is the home of the articles that preceded it.
    const first = groups[0]
    if (first && first.items.length === 0) first.items = leading
    else groups.unshift({ key: 'leading', label: 'DISPOSICIONES GENERALES', subtitle: null, items: leading })
  }

  return groups.filter(group => group.items.length > 0)
}

export function useTargetSummary(
  target: Ref<TargetDocument | null | undefined>,
  sections: Ref<Section[] | null | undefined>
) {
  const blocks = computed<SummaryBlocks>(() => parseSummary(target.value?.summary))

  const hasSummary = computed(() => Object.keys(blocks.value).length > 0)

  const coverage = computed<CoverageStat | null>(() => {
    const stats = target.value?.stats
    if (!stats) return null
    const perSection = stats.distribution.per_section
    return {
      pct: Math.round(stats.coverage.pct_sections_matched * 100),
      sectionsMatched: perSection.filter(s => s.alto + s.medio > 0).length,
      sectionsTotal: perSection.length,
      proposalsIncorporated: stats.coverage.unique_proposals,
      proposalsTotal: stats.coverage.total_proposals,
      alto: stats.degree.alto.count,
      medio: stats.degree.medio.count
    }
  })

  const sectionCounts = computed(() => {
    const map = new Map<number, { alto: number, medio: number }>()
    for (const entry of target.value?.stats?.distribution.per_section ?? []) {
      map.set(entry.section_id, { alto: entry.alto, medio: entry.medio })
    }
    return map
  })

  const groups = computed<LinkageGroup[]>(() =>
    buildGroups(sections.value ?? [], sectionCounts.value)
  )

  const items = computed(() => groups.value.flatMap(group => group.items))

  const maxTotal = computed(() => Math.max(1, ...items.value.map(item => item.total)))

  const orphanSections = computed<OrphanSection[]>(() =>
    items.value
      .filter(item => item.total === 0)
      .map(item => ({ sectionId: item.sectionId, label: item.label, title: item.title }))
  )

  /** Maps `Artículo 4. ... (p. 18)` onto the outline to get `ART. 4 · TÍTULO I`. */
  const highlights = computed<ResolvedHighlight[]>(() =>
    parseHighlights(blocks.value.highlights).map((highlight) => {
      const number = ARTICLE_NUMBER_RE.exec(highlight.sectionRef)?.[1]
      const group = number
        ? groups.value.find(candidate =>
            candidate.items.some(item => item.articleNumber === number)
          )
        : undefined

      const shortRef = number && group
        ? `Art. ${number} · ${group.label}`
        : collapseSpaces(highlight.sectionRef.replace(PAGE_SUFFIX_RE, ''))

      return { ...highlight, shortRef }
    })
  )

  return {
    blocks,
    hasSummary,
    coverage,
    groups,
    maxTotal,
    orphanSections,
    highlights
  }
}
