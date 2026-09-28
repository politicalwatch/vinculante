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

export function topicCssVar(key: TopicKey): `--ed-topic-${TopicKey}` {
  return `--ed-topic-${key}`
}

/** The swatch for a target's `topic`; unknown or missing topics fall back to the first one. */
export function topicOf(topic: string | null): TopicSwatch {
  const entry = TOPIC_PALETTE.find(item => item.key === topic) ?? TOPIC_PALETTE[0]!
  return { ...entry, cssVar: topicCssVar(entry.key) }
}
