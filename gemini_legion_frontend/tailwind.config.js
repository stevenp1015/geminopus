/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'legion-primary': '#6366f1',    // Indigo
        'legion-secondary': '#8b5cf6',  // Purple
        'legion-accent': '#ec4899',     // Pink
        'legion-dark': '#1e1b4b',       // Dark indigo
        'legion-darker': '#0f0a2a',     // Darker indigo
        'minion-happy': '#10b981',      // Emerald
        'minion-neutral': '#6b7280',    // Gray
        'minion-stressed': '#ef4444',   // Red
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'float': 'float 6s ease-in-out infinite',
        'glow': 'glow 2s ease-in-out infinite',
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-10px)' },
        },
        glow: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.5' },
        },
      },
    },
  },
  plugins: [],
}