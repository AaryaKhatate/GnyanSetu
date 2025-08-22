/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./public/index.html",
    "./src/**/*.{js,jsx,ts,tsx}"
  ],
  theme: {
    extend: {
      keyframes: {
        blob: {
          '0%': { transform: 'translate(0px, 0px) scale(1)' },
          '33%': { transform: 'translate(30px, -50px) scale(1.1)' },
          '66%': { transform: 'translate(-20px, 20px) scale(0.95)' },
          '100%': { transform: 'translate(0px, 0px) scale(1)' }
        }
      },
      animation: {
        blob: 'blob 14s ease-in-out infinite'
      },
      colors: {
        background: '#0F172A',
        accentBlue: '#3B82F6',
        accentPurple: '#8B5CF6'
      }
    }
  },
  plugins: []
};


