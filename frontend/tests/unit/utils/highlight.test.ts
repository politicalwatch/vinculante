import { describe, it, expect, beforeEach } from 'vitest'
import { highlightQuotes, removeHighlights } from '../../../app/utils/highlight'

function makeDiv(html: string): HTMLElement {
  const el = document.createElement('div')
  el.innerHTML = html
  return el
}

describe('highlightQuotes', () => {
  it('wraps an exact substring in a single text node with <mark>', () => {
    const el = makeDiv('Hello world')
    highlightQuotes(el, ['Hello world'])
    expect(el.querySelectorAll('mark').length).toBe(1)
    expect(el.textContent).toBe('Hello world')
  })

  it('is case-insensitive', () => {
    const el = makeDiv('Hello World')
    highlightQuotes(el, ['HELLO WORLD'])
    expect(el.querySelectorAll('mark').length).toBe(1)
  })

  it('is diacritic-insensitive', () => {
    const el = makeDiv('El río corre')
    highlightQuotes(el, ['el rio corre'])
    expect(el.querySelectorAll('mark').length).toBeGreaterThanOrEqual(1)
  })

  it('collapses multiple whitespace when matching', () => {
    const el = makeDiv('foo   bar\nbaz')
    highlightQuotes(el, ['foo bar baz'])
    expect(el.querySelectorAll('mark').length).toBeGreaterThanOrEqual(1)
  })

  it('highlights across sibling text nodes (cross-node span)', () => {
    const el = document.createElement('div')
    const p1 = document.createElement('p')
    p1.textContent = 'start of the '  // trailing space bridges the node boundary
    const p2 = document.createElement('p')
    p2.textContent = 'quote end here'
    el.append(p1, p2)
    highlightQuotes(el, ['start of the quote end here'])
    expect(el.querySelectorAll('mark').length).toBeGreaterThanOrEqual(1)
  })

  it('skips quotes shorter than 5 normalized chars', () => {
    const el = makeDiv('go do it')
    highlightQuotes(el, ['go', 'do'])
    expect(el.querySelectorAll('mark').length).toBe(0)
  })

  it('does nothing when the quote is not found in the DOM', () => {
    const el = makeDiv('Some content here')
    highlightQuotes(el, ['this is not present'])
    expect(el.querySelectorAll('mark').length).toBe(0)
    expect(el.textContent).toBe('Some content here')
  })

  it('highlights multiple quotes in a single call', () => {
    const el = makeDiv('alpha and beta and gamma')
    highlightQuotes(el, ['alpha and beta', 'beta and gamma'])
    expect(el.querySelectorAll('mark').length).toBeGreaterThanOrEqual(1)
  })
})

describe('removeHighlights', () => {
  it('removes all <mark> elements and restores original text', () => {
    const el = makeDiv('Hello world')
    highlightQuotes(el, ['Hello world'])
    expect(el.querySelectorAll('mark').length).toBe(1)
    removeHighlights(el)
    expect(el.querySelectorAll('mark').length).toBe(0)
    expect(el.textContent).toBe('Hello world')
  })

  it('highlight → remove → highlight again is idempotent', () => {
    const el = makeDiv('Test phrase here')
    highlightQuotes(el, ['Test phrase here'])
    removeHighlights(el)
    highlightQuotes(el, ['Test phrase here'])
    expect(el.querySelectorAll('mark').length).toBe(1)
    expect(el.textContent).toBe('Test phrase here')
  })
})

describe('highlightQuotes — edge cases', () => {
  it('swallows surroundContents errors on mixed-content ranges without throwing', () => {
    // A quote that crosses a tag boundary cannot use surroundContents but should not throw
    const el = document.createElement('div')
    el.innerHTML = '<strong>bold</strong> normal text and more here'
    expect(() => highlightQuotes(el, ['bold normal text and more here'])).not.toThrow()
  })
})

describe('highlightQuotes — block-boundary and list-marker fallback', () => {
  it('matches across <p> block boundaries (paragraph break normalized to space)', () => {
    const el = makeDiv('<p>first paragraph end.</p><p>second paragraph start</p>')
    highlightQuotes(el, ['first paragraph end. second paragraph start'])
    expect(el.querySelectorAll('mark').length).toBeGreaterThanOrEqual(1)
  })

  it('falls back to a prefix match when quote ends with text from a list marker', () => {
    // "4" is the CSS-generated ::marker of <ol start="4"> — not a DOM text node.
    // The span captures text up to and including "4", but the mark should still appear
    // covering everything up to the boundary ("some text ending here.").
    const el = makeDiv('<p>some text ending here.</p><ol start="4"><li>next item</li></ol>')
    highlightQuotes(el, ['some text ending here. 4'])
    expect(el.querySelectorAll('mark').length).toBeGreaterThanOrEqual(1)
    expect(el.querySelector('mark')?.textContent).toContain('ending here')
  })

  it('falls back to a suffix match when quote starts with text from a list marker', () => {
    // Symmetric: the leading "4." comes from a list marker, so trim from start.
    const el = makeDiv('<ol start="4"><li>item content here and some more words</li></ol><p>following paragraph text.</p>')
    highlightQuotes(el, ['4. item content here and some more words following paragraph text.'])
    expect(el.querySelectorAll('mark').length).toBeGreaterThanOrEqual(1)
  })

  it('does nothing when neither exact nor fallback trimming finds a match', () => {
    const el = makeDiv('<p>totally unrelated content here.</p>')
    highlightQuotes(el, ['this quote shares absolutely no substring at all'])
    expect(el.querySelectorAll('mark').length).toBe(0)
  })
})
