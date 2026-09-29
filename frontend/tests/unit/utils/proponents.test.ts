import { describe, it, expect } from 'vitest'
import { buildProponentOptions, matchesProponent } from '../../../app/utils/proponents'

const talento = { authors: ['Talento para el Futuro', 'Harmon', 'Political Watch'] }
const harmon = { authors: ['Harmon'] }
const comite = { authors: ['Comité de Personas Expertas'] }
const anonymous = { authors: [] as string[] }

describe('matchesProponent', () => {
  it('passes everything for "all"', () => {
    expect(matchesProponent(anonymous, 'all')).toBe(true)
  })

  it('matches when any author is the selected one', () => {
    expect(matchesProponent(talento, 'Harmon')).toBe(true)
    expect(matchesProponent(talento, 'Political Watch')).toBe(true)
    expect(matchesProponent(comite, 'Harmon')).toBe(false)
    expect(matchesProponent(anonymous, 'Harmon')).toBe(false)
  })
})

describe('buildProponentOptions', () => {
  it('is undefined only when no proposal has an author', () => {
    expect(buildProponentOptions([anonymous, anonymous], [anonymous])).toBeUndefined()
    expect(buildProponentOptions([], [])).toBeUndefined()
  })

  it('lists a single author, so the filter still names who made the proposals', () => {
    expect(buildProponentOptions([comite, comite, anonymous], [comite, anonymous])).toEqual([
      { label: 'Todos', value: 'all', count: 2 },
      { label: 'Comité de Personas Expertas', value: 'Comité de Personas Expertas', count: 1 }
    ])
  })

  it('lists every distinct author, counting multi-author proposals for each', () => {
    const options = buildProponentOptions([talento, harmon, comite], [talento, harmon, comite])

    expect(options).toEqual([
      { label: 'Todos', value: 'all', count: 3 },
      { label: 'Harmon', value: 'Harmon', count: 2 },
      { label: 'Comité de Personas Expertas', value: 'Comité de Personas Expertas', count: 1 },
      { label: 'Political Watch', value: 'Political Watch', count: 1 },
      { label: 'Talento para el Futuro', value: 'Talento para el Futuro', count: 1 }
    ])
  })

  it('keeps the list and order from the whole law while counts follow the pool', () => {
    const all = [talento, harmon, comite]
    const options = buildProponentOptions(all, [comite])!

    expect(options.map(option => option.value)).toEqual(
      buildProponentOptions(all, all)!.map(option => option.value)
    )
    expect(options.find(option => option.value === 'Harmon')!.count).toBe(0)
    expect(options.find(option => option.value === 'all')!.count).toBe(1)
  })

  it('counts an author repeated in one proposal once', () => {
    const options = buildProponentOptions([{ authors: ['A', 'A'] }, { authors: ['B'] }], [{ authors: ['A', 'A'] }])!
    expect(options.find(option => option.value === 'A')!.count).toBe(1)
  })
})
