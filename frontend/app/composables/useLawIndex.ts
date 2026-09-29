import type { TargetListItem } from '~/types/api'

/**
 * The catalogue of available laws. The explicit key lets the header and the
 * index page share a single request instead of each getting its own auto-key.
 */
export function useLawIndex() {
  const api = useApi()
  return useFetch<TargetListItem[]>('/targets', {
    $fetch: api,
    key: 'targets'
  })
}
