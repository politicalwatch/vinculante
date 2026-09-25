// https://nuxt.com/docs/api/configuration/nuxt-config

// GA4 measurement ID. Read at build time too: the cookie-control config below
// needs it to name the `_ga_<id>` cookie.
const gtagId = process.env.NUXT_PUBLIC_GTAG_ID ?? ''
const cookiePolicyUrl = 'https://politicalwatch.es/politica-de-cookies/'
export default defineNuxtConfig({
  modules: ['@nuxt/eslint', '@nuxt/ui', '@nuxtjs/mdc', '@nuxtjs/seo', '@nuxt/scripts', '@dargmuesli/nuxt-cookie-control'],

  devtools: {
    enabled: true
  },

  css: ['~/assets/css/main.css'],

  // Nuxt SEO: shared site identity. Set NUXT_SITE_URL in production so og:image resolves to an absolute URL
  site: {
    name: 'Vinculante.ai'
  },
  runtimeConfig: {
    public: {
      apiBase: 'http://localhost:8000',
      // Google Analytics 4 measurement ID (`G-...`). Empty: no banner, no analytics.
      gtagId
    }
  },
  routeRules: {
    '/experimental/**': {
      ssr: false,
      isr: false
    }
  },

  compatibilityDate: '2025-01-15',

  // Same setup as the vinculante.ai landing (AEPD tweaks included), Spanish only.
  cookieControl: {
    locales: ['es'],
    // 6-month consent expiry (AEPD guidance) instead of the 1-year default
    cookieExpiryOffsetMs: 1000 * 60 * 60 * 24 * 180,
    barPosition: 'bottom-left',
    // The footer "Cookie settings" link reopens the panel instead of a floating button
    isControlButtonEnabled: false,
    localeTexts: {
      es: {
        // The default says continuing to browse means consent: not valid under the AEPD guide
        bannerDescription: 'Usamos Google Analytics para conocer el impacto de Vinculante.ai y seguir mejorándolo. Solo lo activamos si lo aceptas. Puedes aceptarlo, rechazarlo o configurar tus preferencias, y cambiar de opinión cuando quieras desde el pie de página.',
        // Unambiguous reject labels (defaults: "Acepto lo necesario" / "Rechazar todo")
        decline: 'Rechazar',
        declineAll: 'Rechazar todo'
      }
    },
    // The vinculante.ai landing's resolved Nuxt UI tokens. They can't be `var(--ui-*)` here as on
    // the landing: the module sets these on <html>, where this app's tokens (blue primary, slate
    // surfaces) would win. Teal primary, cream paper, indigo ink.
    colors: {
      barBackground: '#ffffff',
      barTextColor: '#314158',
      barButtonBackground: '#2a8e8e',
      barButtonColor: '#faf7f2',
      barButtonHoverBackground: '#29235c',
      barButtonHoverColor: '#faf7f2',
      modalBackground: '#ffffff',
      modalTextColor: '#314158',
      modalButtonBackground: '#2a8e8e',
      modalButtonColor: '#faf7f2',
      modalButtonHoverBackground: '#29235c',
      modalButtonHoverColor: '#faf7f2',
      modalOverlay: '#29235c',
      modalOverlayOpacity: 0.6,
      modalUnsavedColor: '#faf7f2',
      checkboxActiveBackground: '#2a8e8e',
      checkboxActiveCircleBackground: '#faf7f2',
      checkboxInactiveBackground: '#dcd7ce',
      checkboxInactiveCircleBackground: '#faf7f2',
      checkboxDisabledBackground: '#e7e2da',
      checkboxDisabledCircleBackground: '#faf7f2',
      focusRingColor: '#2a8e8e'
    },
    cookies: {
      necessary: [
        {
          id: 'consent',
          name: 'Preferencias de cookies',
          description: 'Guardan tu elección en este panel.',
          targetCookieIds: ['ncc_c', 'ncc_e']
        }
      ],
      optional: [
        {
          id: 'ga',
          name: 'Google Analytics',
          description: 'Cookies de analítica. Nos ayudan a entender cómo se usa el sitio.',
          // Key is the URL, value the label (qhld.es has them swapped)
          links: { [cookiePolicyUrl]: 'politicalwatch.es/politica-de-cookies' },
          targetCookieIds: ['_ga', ...(gtagId ? [`_ga_${gtagId.replace(/^G-/, '')}`] : [])]
        }
      ]
    }
  },

  eslint: {
    config: {
      stylistic: {
        commaDangle: 'never',
        braceStyle: '1tbs'
      }
    }
  },

})  ogImage: {
    // The social card is a static image shared with vinculante.ai: public/og-image.png
    enabled: false
  }

})
