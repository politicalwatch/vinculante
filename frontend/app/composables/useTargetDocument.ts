import type { TargetDocument } from '~/types/api'

/**
 * A single target document. The explicit key is shared by every caller for the
 * same id, so moving between the summary and the detail view reuses the payload.
 */
export function useTargetDocument(id: number) {
  const api = useApi()
  return useFetch<TargetDocument>(`/targets/${id}`, {
    $fetch: api,
    key: `target-${id}`
  })
}
