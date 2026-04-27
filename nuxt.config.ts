// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  modules: [
    '@nuxt/eslint',
    '@nuxt/ui',
    '@comark/nuxt',
    '@nuxthub/core',
    'nuxt-auth-utils',
    'nuxt-charts',
    'nuxt-csurf',
    'nuxt-skill-hub'
  ],

  devtools: {
    enabled: true
  },

  css: ['~/assets/css/main.css'],

  experimental: {
    viewTransition: true
  },

  colorMode: {
    preference: 'dark'
  },

  compatibilityDate: '2024-07-11',

  runtimeConfig: {
    flaskApiUrl: process.env.FLASK_API_URL || 'http://localhost:5001',
    ssoClientId: process.env.NUXT_SSO_CLIENT_ID || '',
    ssoClientSecret: process.env.NUXT_SSO_CLIENT_SECRET || '',
    ssoAuthorizeUrl: process.env.NUXT_SSO_AUTHORIZE_URL || '',
    ssoTokenUrl: process.env.NUXT_SSO_TOKEN_URL || '',
    ssoUserinfoUrl: process.env.NUXT_SSO_USERINFO_URL || '',
    ssoRedirectUrl: process.env.NUXT_SSO_REDIRECT_URL || '',
    tokenExchangeUrl: process.env.NUXT_TOKEN_EXCHANGE_URL || '',
    ssoCookieName: process.env.NUXT_SSO_COOKIE_NAME || 'sso_token'
  },

  nitro: {
    experimental: {
      openAPI: true
    }
  },

  hub: {
    db: 'sqlite',
    blob: true
  },

  fonts: {
    providers: {
      google: false,
      googleicons: false
    }
  },

  vite: {
    optimizeDeps: {
      include: ['striptags']
    }
  },

  eslint: {
    config: {
      stylistic: {
        commaDangle: 'never',
        braceStyle: '1tbs'
      }
    }
  }
})