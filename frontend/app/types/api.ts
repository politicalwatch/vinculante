export type MatchDegree = 'alto' | 'medio' | 'bajo' | 'ninguno'
export type MatchStatus = 'pending' | 'confirmed' | 'rejected'

export interface ConfidenceStats {
  mean: number | null
  median: number | null
  p25: number | null
  p75: number | null
}

export interface TargetStats {
  coverage: {
    pct_sections_matched: number
    orphan_sections: number
    total_matches: number
    unique_proposals: number
    total_proposals: number
  }
  degree: {
    alto: { count: number; pct: number }
    medio: { count: number; pct: number }
  }
  confidence: ConfidenceStats & {
    by_degree: { alto: ConfidenceStats; medio: ConfidenceStats }
  }
  distribution: {
    histogram: { '0': number; '1': number; '2': number; '3+': number }
    avg_matches_per_matched_section: number | null
    per_section: Array<{ section_id: number; alto: number; medio: number }>
  }
  quality: {
    pct_with_spans: number
    top_proposals: Array<{ proposal_id: number; count: number }>
  }
}

export interface TargetDocument {
  id: number
  title: string
  author: string
  date: string | null
  version: string | null
  proposal_count: number
  match_count: number
  stats: TargetStats | null
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
