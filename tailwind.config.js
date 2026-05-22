module.exports = {
  content: [
    './frontend/templates/**/*.html',
    './frontend/src/**/*.js',
    './core/**/*.py',
  ],
  theme: {
    extend: {
      colors: {
        ink: 'oklch(0.19 0.035 145)',
        'ink-soft': 'oklch(0.38 0.03 145)',
        muted: 'oklch(0.48 0.025 145)',
        page: 'oklch(0.965 0.015 125)',
        paper: 'oklch(0.992 0.006 100)',
        'paper-strong': 'oklch(0.982 0.011 105)',
        line: 'oklch(0.855 0.027 118)',
        'line-strong': 'oklch(0.74 0.035 122)',
        accent: 'oklch(0.68 0.18 48)',
        'accent-dark': 'oklch(0.48 0.15 45)',
        'accent-soft': 'oklch(0.96 0.045 62)',
        cobalt: 'oklch(0.48 0.14 242)',
        'cobalt-soft': 'oklch(0.93 0.035 242)',
        danger: 'oklch(0.56 0.18 25)',
        'danger-soft': 'oklch(0.94 0.045 25)',
        success: 'oklch(0.49 0.12 150)',
        'success-soft': 'oklch(0.93 0.045 150)',
        warning: 'oklch(0.38 0.09 72)',
        'warning-soft': 'oklch(0.95 0.055 85)',
      },
      boxShadow: {
        input: 'inset 0 1px 0 oklch(0.995 0.004 100 / 0.42)',
        low: '0 1px 0 oklch(0.19 0.035 145 / 0.08)',
        mid: '0 1px 0 oklch(0.19 0.035 145 / 0.12), 0 8px 0 oklch(0.19 0.035 145 / 0.03)',
        emblem: 'inset 0 0 0 1px oklch(0.68 0.18 48 / 0.16)',
      },
      backgroundImage: {
        'page-grid': 'linear-gradient(oklch(0.19 0.035 145 / 0.035) 1px, transparent 1px), linear-gradient(90deg, oklch(0.19 0.035 145 / 0.03) 1px, transparent 1px)',
        'signal-panel': 'linear-gradient(135deg, oklch(0.992 0.006 100) 0%, oklch(0.94 0.03 140) 100%)',
        'signal-grid': 'linear-gradient(90deg, oklch(0.19 0.035 145 / 0.06) 1px, transparent 1px), linear-gradient(oklch(0.19 0.035 145 / 0.06) 1px, transparent 1px)',
      },
      fontFamily: {
        sans: ['ui-sans-serif', '-apple-system', 'BlinkMacSystemFont', '"Segoe UI"', 'system-ui', 'sans-serif'],
      },
      keyframes: {
        'line-draw': {
          to: { strokeDashoffset: '0' },
        },
      },
      animation: {
        'line-draw': 'line-draw 1200ms cubic-bezier(0.19, 1, 0.22, 1) forwards',
      },
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
    require('@tailwindcss/forms'),
  ],
};
