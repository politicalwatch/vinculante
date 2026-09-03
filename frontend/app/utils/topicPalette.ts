export const TOPIC_PALETTE = [
  { key: 'digitales', label: 'Entornos digitales' },
  { key: 'movilidad', label: 'Movilidad' },
  { key: 'clima', label: 'Clima' },
  { key: 'educacion', label: 'Educación' },
  { key: 'vivienda', label: 'Vivienda' },
  { key: 'salud', label: 'Salud' },
  { key: 'empleo', label: 'Empleo' },
  { key: 'justicia', label: 'Justicia' },
  { key: 'igualdad', label: 'Igualdad' },
  { key: 'cultura', label: 'Cultura' }
] as const

export type TopicKey = typeof TOPIC_PALETTE[number]['key']

export type TopicSwatch = typeof TOPIC_PALETTE[number] & {
  cssVar: `--ed-topic-${TopicKey}`
}

/** Hardcoded for this gallery test — not fetched from the API. */
export const TARGET_TOPIC: Record<number, TopicKey> = {
  43: 'digitales',
  40: 'digitales',
  35: 'digitales',
  10: 'movilidad',
  8: 'clima',
  2: 'educacion',
  1: 'vivienda'
}

export function topicCssVar(key: TopicKey): `--ed-topic-${TopicKey}` {
  return `--ed-topic-${key}`
}

export function topicOf(targetId: number): TopicSwatch {
  const key = TARGET_TOPIC[targetId] ?? 'digitales'
  const entry = TOPIC_PALETTE.find(topic => topic.key === key) ?? TOPIC_PALETTE[0]!
  return { ...entry, cssVar: topicCssVar(entry.key) }
}