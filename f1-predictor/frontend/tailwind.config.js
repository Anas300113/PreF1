/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        f1: {
          red: '#E10600',
          redDeep: '#A80400',
          dark: '#08090C',
          panel: '#0E1116',
          surface: '#15191F',
          elevated: '#1B2027',
          border: 'rgba(255,255,255,0.08)',
          gold: '#F5B942',
          silver: '#9BA1AA',
          bronze: '#CD7F32',
        },
        ink: {
          primary: '#F5F6F7',
          secondary: '#9BA1AA',
          muted: '#636973',
        },
        sector: {
          purple: '#A855F7',
          green: '#20C997',
          yellow: '#F5B942',
        },
      },
      fontFamily: {
        display: ['"Space Grotesk"', 'Inter', 'system-ui', 'sans-serif'],
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['"JetBrains Mono"', '"SF Mono"', 'ui-monospace', 'Menlo', 'monospace'],
      },
      boxShadow: {
        panel: '0 1px 0 rgba(255,255,255,0.04) inset, 0 8px 24px rgba(0,0,0,0.35)',
        pop: '0 12px 40px rgba(0,0,0,0.5)',
      },
      borderRadius: {
        sm2: '6px',
        md2: '10px',
        lg2: '14px',
      },
    },
  },
  plugins: [],
}
