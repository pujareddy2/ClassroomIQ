import type { Config } from 'tailwindcss'

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        canvas: 'hsl(var(--canvas))', surface: 'hsl(var(--surface))', elevated: 'hsl(var(--elevated))',
        ink: 'hsl(var(--ink))', muted: 'hsl(var(--muted))', line: 'hsl(var(--line))',
        brand: { DEFAULT: 'hsl(var(--brand))', soft: 'hsl(var(--brand-soft))' },
        success: 'hsl(var(--success))', warning: 'hsl(var(--warning))', danger: 'hsl(var(--danger))', info: 'hsl(var(--info))'
      },
      borderRadius: { xl: '0.75rem', '2xl': '1rem', '3xl': '1.5rem' },
      boxShadow: { soft: '0 8px 30px rgb(15 23 42 / 0.06)', float: '0 18px 50px rgb(15 23 42 / 0.12)' }
    }
  }, plugins: []
} satisfies Config
