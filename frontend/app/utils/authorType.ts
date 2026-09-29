const AUTHOR_TYPE_LABELS: Record<string, string> = {
  citizen: 'Ciudadanía',
  academia: 'Grupo de expertos'
}

export function authorTypeLabel(authorType: string | null | undefined): string | null {
  if (!authorType) return null
  return AUTHOR_TYPE_LABELS[authorType] ?? authorType
}
