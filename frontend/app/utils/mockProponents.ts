import type { Proposal } from '~/types/api'
import { mulberry32 } from '~/utils/random'

/**
 * Stand-in for organisation/proponent metadata the client has but that is not
 * yet exposed by the API. Deterministic so the assignment survives reloads.
 */
export const PROPONENTS = [
  'Asociación Vecinal Centro',
  'Fundación Horizonte Verde',
  'Colegio de Arquitectos',
  'Plataforma Movilidad Sostenible',
  'Cámara de Comercio Local',
  'Observatorio Urbano',
  'Red de Barrios Unidos',
  'Instituto de Estudios Urbanos',
  'Colectivo Espacio Público',
  'Federación de Comerciantes'
] as const

const MIN_CHUNK = 3
const MAX_CHUNK = 7

/** Assign 3–7 proposals to each organisation in a deterministic round-robin. */
export function assignProponents(proposals: Proposal[]): Map<number, string> {
  const result = new Map<number, string>()
  if (proposals.length === 0) return result

  const shuffled = proposals
    .map(proposal => ({
      id: proposal.id,
      sort: mulberry32(proposal.id * 2654435761 + 41)()
    }))
    .sort((a, b) => a.sort - b.sort)

  let cursor = 0
  let orgIndex = 0

  while (cursor < shuffled.length) {
    const random = mulberry32(orgIndex * 97 + shuffled.length + 13)
    const chunkSize = Math.min(
      shuffled.length - cursor,
      MIN_CHUNK + Math.floor(random() * (MAX_CHUNK - MIN_CHUNK + 1))
    )
    const name = PROPONENTS[orgIndex % PROPONENTS.length]!
    for (let i = 0; i < chunkSize; i++) {
      const entry = shuffled[cursor + i]
      if (entry) result.set(entry.id, name)
    }
    cursor += chunkSize
    orgIndex += 1
  }

  return result
}
