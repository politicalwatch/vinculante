interface CharEntry {
  node: Text
  offset: number
}

const BLOCK_TAGS = new Set(['P', 'DIV', 'LI', 'TD', 'TH', 'H1', 'H2', 'H3', 'H4', 'H5', 'H6', 'BLOCKQUOTE', 'PRE'])

function blockAncestor(node: Node): Node | null {
  let n = node.parentNode
  while (n) {
    if (n.nodeType === Node.ELEMENT_NODE && BLOCK_TAGS.has((n as Element).tagName)) return n
    n = n.parentNode
  }
  return null
}

function buildDomIndex(root: HTMLElement): { norm: string; map: CharEntry[] } {
  const norm: string[] = []
  const map: CharEntry[] = []
  let prevSpace = true
  let prevBlock: Node | null = null

  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT)
  let node: Text | null
  while ((node = walker.nextNode() as Text | null)) {
    // Inject a space at block element boundaries so paragraph breaks in raw text
    // (which normalizeQuery turns into a space) match the DOM's block transitions.
    const curBlock = blockAncestor(node)
    if (prevBlock !== null && curBlock !== prevBlock && !prevSpace) {
      norm.push(' ')
      map.push({ node, offset: 0 })
      prevSpace = true
    }
    prevBlock = curBlock

    const text = node.nodeValue ?? ''
    for (let i = 0; i < text.length; i++) {
      const ch = text[i]
      for (const sub of ch.normalize('NFKD')) {
        if (/\p{M}/u.test(sub)) continue
        const c = sub.toLowerCase()
        if (/\s/.test(c)) {
          if (!prevSpace && norm.length) {
            norm.push(' ')
            map.push({ node, offset: i })
            prevSpace = true
          }
        } else {
          norm.push(c)
          map.push({ node, offset: i })
          prevSpace = false
        }
      }
    }
  }
  while (norm.length && norm[norm.length - 1] === ' ') {
    norm.pop()
    map.pop()
  }
  return { norm: norm.join(''), map }
}

function normalizeQuery(q: string): string {
  const out: string[] = []
  let prevSpace = true
  for (const ch of q) {
    for (const sub of ch.normalize('NFKD')) {
      if (/\p{M}/u.test(sub)) continue
      const c = sub.toLowerCase()
      if (/\s/.test(c)) {
        if (!prevSpace && out.length) { out.push(' '); prevSpace = true }
      } else {
        out.push(c); prevSpace = false
      }
    }
  }
  while (out.length && out[out.length - 1] === ' ') out.pop()
  return out.join('')
}

function wrapRange(startNode: Text, startOff: number, endNode: Text, endOff: number): void {
  const applyMark = (node: Text, from: number, to: number) => {
    try {
      const range = document.createRange()
      range.setStart(node, from)
      range.setEnd(node, to)
      const mark = document.createElement('mark')
      mark.className = 'bg-yellow-200 dark:bg-yellow-500/30 text-inherit rounded-sm p-0'
      range.surroundContents(mark)
    } catch { /* skip if node has mixed content */ }
  }

  if (startNode === endNode) {
    applyMark(startNode, startOff, endOff)
    return
  }
  // Span crosses node boundaries — mark each node fragment individually
  applyMark(startNode, startOff, startNode.length)
  applyMark(endNode, 0, endOff)
}

export function removeHighlights(root: HTMLElement): void {
  root.querySelectorAll('mark.bg-yellow-200').forEach((mark) => {
    const parent = mark.parentNode
    if (!parent) return
    while (mark.firstChild) parent.insertBefore(mark.firstChild, mark)
    parent.removeChild(mark)
    parent.normalize()
  })
}

function findRange(norm: string, normQ: string): { pos: number; end: number } | null {
  const MIN = 20
  let pos = norm.indexOf(normQ)
  if (pos >= 0) return { pos, end: pos + normQ.length }
  // Trim trailing tokens — handles spans that end inside a list marker or other
  // marker-only element whose text is never emitted as a DOM text node.
  let q = normQ
  while (q.length > MIN) {
    const lastSpace = q.lastIndexOf(' ')
    if (lastSpace <= 0) break
    q = q.slice(0, lastSpace)
    pos = norm.indexOf(q)
    if (pos >= 0) return { pos, end: pos + q.length }
  }
  // Trim leading tokens — symmetric fallback for spans that start inside a marker.
  q = normQ
  while (q.length > MIN) {
    const firstSpace = q.indexOf(' ')
    if (firstSpace < 0) break
    q = q.slice(firstSpace + 1)
    pos = norm.indexOf(q)
    if (pos >= 0) return { pos, end: pos + q.length }
  }
  return null
}

export function highlightQuotes(root: HTMLElement, quotes: string[]): void {
  if (!quotes.length) return
  const { norm, map } = buildDomIndex(root)

  const ranges: Array<{ start: number; end: number }> = []
  for (const q of quotes) {
    const normQ = normalizeQuery(q)
    if (normQ.length < 5) continue
    const found = findRange(norm, normQ)
    if (!found) continue
    const { pos, end } = found
    if (!ranges.some(r => pos < r.end && end > r.start)) {
      ranges.push({ start: pos, end })
    }
  }

  // Apply in reverse document order so earlier-position ranges keep valid node references
  // after surroundContents splits text nodes for later (higher-offset) ranges.
  ranges.sort((a, b) => b.start - a.start)
  for (const r of ranges) {
    const s = map[r.start]
    const e = map[r.end - 1]
    if (!s || !e) continue
    wrapRange(s.node, s.offset, e.node, e.offset + 1)
  }
}
