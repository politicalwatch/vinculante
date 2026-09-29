import { describe, it, expect } from 'vitest'
import {
  parseHighlight,
  parseHighlights,
  parseLabelledBullet,
  parseSummary,
  splitPullQuote
} from '../../../app/utils/summaryMarkdown'

const SUMMARY = `## Resumen de la ley

Este proyecto de ley orgánica establece un marco integral para proteger a las personas menores de edad en los entornos digitales. El texto combina medidas preventivas, educativas, sanitarias, asistenciales y regulatorias para promover un uso seguro, saludable y responsable del entorno digital. Además, refuerza la respuesta institucional ante situaciones de violencia digital que afecten a menores.

- Derechos de la infancia en el entorno digital
- Salud, prevención y gobernanza pública

## Resumen de las vinculaciones detectadas

La alineación global es amplia y consistente.

Las áreas con mayor vinculación son:

- **Protección y seguridad digital por diseño**: Existe una convergencia muy fuerte.

## Vinculaciones destacadas

Entre las propuestas académicas, destacan varias vinculaciones.

- **Comité de personas expertas** — Exige imponer sistemas de verificación de edad.. Vinculada con **Artículo 4. Obligaciones de los fabricantes. (p. 18)**: Es especialmente destacable por su alta especificidad técnica.

## Propuestas no recogidas

Las secciones del documento sin vinculación aceptada se concentran en tres frentes.
`

describe('parseSummary', () => {
  it('splits the four known blocks and separates prose from bullets', () => {
    const blocks = parseSummary(SUMMARY)

    expect(Object.keys(blocks)).toEqual(['ley', 'linkages', 'highlights', 'gaps'])
    expect(blocks.ley!.paragraphs).toHaveLength(1)
    expect(blocks.ley!.bullets).toHaveLength(2)
    expect(blocks.linkages!.paragraphs).toHaveLength(2)
    expect(blocks.gaps!.bullets).toHaveLength(0)
  })

  it('returns an empty object when there is no summary', () => {
    expect(parseSummary(null)).toEqual({})
    expect(parseSummary('')).toEqual({})
  })

  it('ignores headings it does not know about', () => {
    const blocks = parseSummary('## Observaciones\n\ntexto\n\n## Resumen de la ley\n\nintro')
    expect(Object.keys(blocks)).toEqual(['ley'])
  })
})

describe('parseLabelledBullet', () => {
  it('splits a bold lead-in from its description', () => {
    const bullet = parseLabelledBullet('- **Vivienda**: Hay convergencia.')
    expect(bullet.label).toBe('Vivienda')
    expect(bullet.text).toBe('Hay convergencia.')
  })

  it('leaves an unlabelled bullet as plain text', () => {
    const bullet = parseLabelledBullet('- Derechos de la infancia')
    expect(bullet.label).toBeNull()
    expect(bullet.text).toBe('Derechos de la infancia')
  })
})

describe('parseHighlight', () => {
  it('extracts author, claim, section reference and relevance', () => {
    const highlight = parseHighlight(
      '- **Comité de expertas** — Exige verificación de edad.. Vinculada con **Artículo 4 (p. 18)**: Es destacable.'
    )

    expect(highlight).toEqual({
      author: 'Comité de expertas',
      claim: 'Exige verificación de edad',
      sectionRef: 'Artículo 4 (p. 18)',
      relevance: 'Es destacable.'
    })
  })

  it('returns null for a bullet that is not a highlight', () => {
    expect(parseHighlight('- **Vivienda**: Hay convergencia.')).toBeNull()
  })

  it('parses every highlight bullet of a summary block', () => {
    const highlights = parseHighlights(parseSummary(SUMMARY).highlights)
    expect(highlights).toHaveLength(1)
    expect(highlights[0]!.sectionRef).toBe('Artículo 4. Obligaciones de los fabricantes. (p. 18)')
  })
})

describe('splitPullQuote', () => {
  it('lifts a framing sentence out of the middle of the paragraph', () => {
    const { before, quote, after } = splitPullQuote(parseSummary(SUMMARY).ley!.paragraphs[0])

    expect(quote).toBe(
      'El texto combina medidas preventivas, educativas, sanitarias, asistenciales y regulatorias para promover un uso seguro, saludable y responsable del entorno digital.'
    )
    expect(before).toMatch(/^Este proyecto de ley orgánica/)
    expect(after).toMatch(/^Además, refuerza/)
  })

  it('never lifts the opening sentence', () => {
    const paragraph = 'Esta ley establece un marco. Una segunda frase corta. Una tercera frase corta.'
    expect(splitPullQuote(paragraph).quote).not.toBe('Esta ley establece un marco.')
  })

  it('leaves short paragraphs untouched', () => {
    const { before, quote, after } = splitPullQuote('Una sola frase.')
    expect(before).toBe('Una sola frase.')
    expect(quote).toBeNull()
    expect(after).toBe('')
  })

  it('handles a missing paragraph', () => {
    expect(splitPullQuote(undefined)).toEqual({ before: '', quote: null, after: '' })
  })
})
