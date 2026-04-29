export type MatchDegree = 'alto' | 'medio' | 'bajo' | 'ninguno'
export type MatchStatus = 'pending' | 'confirmed' | 'rejected'

export interface TargetDocument {
  id: number
  title: string
  author: string
  date: string | null
  version: string | null
  proposal_count: number
  match_count: number
}

export interface Section {
  id: number
  text: string
  text_markdown: string | null
  clear_language: string | null
  page_number: number | null
  section_type: string | null
  section_number: string | null
  parent_id: number | null
  target_id: number
  is_matchable: boolean
}

export interface Proposal {
  id: number
  text: string
  author: string | null
  author_type: string | null
  reference: string | null
  topic: string | null
  subtopic: string | null
  source_file: string | null
}

export interface Match {
  id: number
  proposal_id: number
  section_id: number
  degree: MatchDegree | null
  explanation: string | null
  confidence: number | null
  status: MatchStatus
  section_spans: [number, number][] | null
  proposal: Proposal
}
