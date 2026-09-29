/**
 * Parsing for the LLM-generated `target.summary` markdown.
 *
 * Every summarised law emits the same four `##` headings in the same order, so
 * the screen can split the blob into blocks instead of rendering it as one
 * undifferentiated prose column.
 */

export type SummaryBlockKey = 'ley' | 'linkages' | 'highlights' | 'gaps'

export interface SummaryBullet {
  /** Bold lead-in of a `- **Label**: text` bullet, when present. */
  label: string | null
  text: string
  /** Bullet body with the list marker removed, before any field splitting. */
  raw: string
}

export interface SummaryBlock {
  heading: string
  paragraphs: string[]
  bullets: SummaryBullet[]
}

export type SummaryBlocks = Partial<Record<SummaryBlockKey, SummaryBlock>>

export interface SummaryHighlight {
  author: string
  claim: string
  sectionRef: string
  relevance: string
}

export interface PullQuoteSplit {
  before: string
  quote: string | null
  after: string
}

const BLOCK_KEYS: Array<{ key: SummaryBlockKey, heading: string }> = [
  { key: 'ley', heading: 'resumen de la ley' },
  { key: 'linkages', heading: 'resumen de las vinculaciones detectadas' },
  { key: 'highlights', heading: 'vinculaciones destacadas' },
  { key: 'gaps', heading: 'propuestas no recogidas' }
]

const LABELLED_BULLET_RE = /^\*\*(.+?)\*\*\s*:\s*([\s\S]+)$/

/**
 * `- **{autor}** — {claim}.. Vinculada con **{section_ref}**: {relevance}`
 * The formatter appends its own period to a claim that already ends in one, so
 * the separator before "Vinculada" is tolerated as one or two dots.
 */
const HIGHLIGHT_RE
  = /^\*\*(.+?)\*\*\s*[—–-]\s*([\s\S]+?)\.?\.\s*Vinculada con\s+\*\*(.+?)\*\*\s*:\s*([\s\S]+)$/

/** Sentence-final punctuation followed by whitespace, without splitting "art. 4". */
const SENTENCE_SPLIT_RE = /(?<=[.!?])\s+(?=[¿¡"«A-ZÁÉÍÓÚÑ])/

/** Verbs the model uses when it states what the norm *is*, rather than a detail. */
const FRAMING_VERBS_RE
  = /\b(configura|establece|tiene por objeto|parte de la idea|busca|combina|promueve|introduce|refuerza|regula|articula)\b/i

const QUOTE_MIN_LENGTH = 90
const QUOTE_MAX_LENGTH = 260

function normaliseHeading(heading: string): string {
  return heading.trim().toLowerCase()
}

function stripBulletMarker(line: string): string {
  return line.replace(/^[-*]\s+/, '').trim()
}

export function parseLabelledBullet(line: string): SummaryBullet {
  const raw = stripBulletMarker(line)
  const match = LABELLED_BULLET_RE.exec(raw)
  if (!match) return { label: null, text: raw, raw }
  return { label: match[1]!.trim(), text: match[2]!.trim(), raw }
}

export function parseHighlight(line: string): SummaryHighlight | null {
  const match = HIGHLIGHT_RE.exec(stripBulletMarker(line))
  if (!match) return null
  return {
    author: match[1]!.trim(),
    claim: match[2]!.trim(),
    sectionRef: match[3]!.trim(),
    relevance: match[4]!.trim()
  }
}

/**
 * Splits the summary on `##` headings. Unknown headings are dropped rather than
 * rendered, so a future block cannot break the layout.
 */
export function parseSummary(markdown: string | null | undefined): SummaryBlocks {
  if (!markdown) return {}

  const blocks: SummaryBlocks = {}

  for (const chunk of markdown.split(/^##\s+/m).slice(1)) {
    const newline = chunk.indexOf('\n')
    const heading = (newline === -1 ? chunk : chunk.slice(0, newline)).trim()
    const body = newline === -1 ? '' : chunk.slice(newline + 1)

    const entry = BLOCK_KEYS.find(candidate => candidate.heading === normaliseHeading(heading))
    if (!entry) continue

    const paragraphs: string[] = []
    const bullets: SummaryBullet[] = []

    for (const line of body.split('\n')) {
      const trimmed = line.trim()
      if (!trimmed) continue
      if (/^[-*]\s+/.test(trimmed)) bullets.push(parseLabelledBullet(trimmed))
      else paragraphs.push(trimmed)
    }

    blocks[entry.key] = { heading, paragraphs, bullets }
  }

  return blocks
}

export function parseHighlights(block: SummaryBlock | undefined): SummaryHighlight[] {
  if (!block) return []
  return block.bullets
    .map(bullet => parseHighlight(bullet.raw))
    .filter((highlight): highlight is SummaryHighlight => highlight !== null)
}

export function splitSentences(paragraph: string): string[] {
  return paragraph.split(SENTENCE_SPLIT_RE).map(sentence => sentence.trim()).filter(Boolean)
}

/**
 * Promotes the most defining sentence of the opening paragraph into a pull
 * quote, keeping the surrounding sentences as prose. Scores on framing verbs
 * and on fitting the quote slot, and never lifts the first sentence so the
 * block still opens with running text.
 */
export function splitPullQuote(paragraph: string | undefined): PullQuoteSplit {
  if (!paragraph) return { before: '', quote: null, after: '' }

  const sentences = splitSentences(paragraph)
  if (sentences.length < 3) return { before: paragraph, quote: null, after: '' }

  let bestIndex = -1
  let bestScore = -Infinity

  for (let index = 1; index < sentences.length; index++) {
    const sentence = sentences[index]!
    let score = 0
    if (FRAMING_VERBS_RE.test(sentence)) score += 3
    if (sentence.length >= QUOTE_MIN_LENGTH && sentence.length <= QUOTE_MAX_LENGTH) score += 2
    else if (sentence.length > QUOTE_MAX_LENGTH) score -= 2
    else score -= 1
    // Earlier sentences read as thesis statements; later ones as detail.
    score -= index * 0.25

    if (score > bestScore) {
      bestScore = score
      bestIndex = index
    }
  }

  if (bestIndex === -1) return { before: paragraph, quote: null, after: '' }

  return {
    before: sentences.slice(0, bestIndex).join(' '),
    quote: sentences[bestIndex]!,
    after: sentences.slice(bestIndex + 1).join(' ')
  }
}
