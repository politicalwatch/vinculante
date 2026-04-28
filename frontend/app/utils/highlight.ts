interface CharEntry {
  node: Text
  offset: number
}

function buildDomIndex(root: HTMLElement): { norm: string; map: CharEntry[] } {
  const norm: string[] = []
  const map: CharEntry[] = []
  let prevSpace = true

  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT)
  let node: Text | null
  while ((node = walker.nextNode() as Text | null)) {
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

export function highlightQuotes(root: HTMLElement, quotes: string[]): void {
  if (!quotes.length) return
  const { norm, map } = buildDomIndex(root)

  for (const q of quotes) {
    const normQ = normalizeQuery(q)
    if (normQ.length < 5) continue
    const pos = norm.indexOf(normQ)
    if (pos < 0) continue

    const startEntry = map[pos]
    const endEntry = map[pos + normQ.length - 1]
    if (!startEntry || !endEntry) continue

    wrapRange(startEntry.node, startEntry.offset, endEntry.node, endEntry.offset + 1)
  }
}
