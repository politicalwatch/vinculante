/**
 * Ties the cookie-control "ga" category to Google Analytics.
 * Unlike qhld.es, gtag.js is not requested at all until the visitor accepts,
 * and only analytics storage is granted (advertising stays denied).
 */
export default defineNuxtPlugin(() => {
  const gtagId = useRuntimeConfig().public.gtagId as string
  if (!gtagId) return

  const { cookiesEnabledIds, isConsentGiven } = useCookieControl()
  // `cookiesEnabledIds` is read raw from the `ncc_e` cookie, while `isConsentGiven`
  // is only true if the stored consent matches the current cookie list. After the
  // list changes (or with a stale cookie) the banner is back but `ncc_e` may still
  // say "ga", so both are required.
  const consented = computed(() =>
    isConsentGiven.value === true && (cookiesEnabledIds.value?.includes('ga') ?? false)
  )

  const { proxy } = useScriptGoogleAnalytics({
    id: gtagId,
    // Only reached after consent, so analytics can start as granted.
    defaultConsent: {
      analytics_storage: 'granted',
      ad_storage: 'denied',
      ad_user_data: 'denied',
      ad_personalization: 'denied'
    },
    scriptOptions: {
      trigger: useScriptTriggerConsent({ consent: consented })
    }
  })

  watch(consented, (value, previous) => {
    if (!previous || value) return
    proxy.gtag('consent', 'update', { analytics_storage: 'denied' })
    removeAnalyticsCookies()
  })
})

// cookie-control deletes `targetCookieIds` only on the current host, but GA
// writes them on the registrable domain (`.vinculante.ai`), so clear every level.
function removeAnalyticsCookies() {
  const names = document.cookie
    .split(';')
    .map(cookie => cookie.split('=')[0]!.trim())
    .filter(name => name === '_ga' || name.startsWith('_ga_'))
  const labels = location.hostname.split('.')
  const domains = labels.map((_, index) => labels.slice(index).join('.'))

  for (const name of names) {
    document.cookie = `${name}=; Max-Age=0; path=/`
    for (const domain of domains) {
      document.cookie = `${name}=; Max-Age=0; path=/; domain=${domain}`
    }
  }
}
