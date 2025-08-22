/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./public/index.html",
    "./src/**/*.{js,jsx,ts,tsx}"
  ],
  theme: {
    extend: {
      colors: {
        background: {
          DEFAULT: "#0F172A",
          soft: "#1E293B"
        }
      },
      boxShadow: {
        glow: "0 0 20px rgba(99, 102, 241, 0.35)",
        glow2: "0 0 30px rgba(59, 130, 246, 0.25)"
      },
      keyframes: {
        float: {
          '0%': { transform: 'translateY(0px) scale(1)' },
          '50%': { transform: 'translateY(-10px) scale(1.02)' },
          '100%': { transform: 'translateY(0px) scale(1)' }
        },
        blob: {
          '0%': { transform: 'translate(0px, 0px) scale(1)' },
          '33%': { transform: 'translate(20px, -30px) scale(1.1)' },
          '66%': { transform: 'translate(-20px, 10px) scale(0.9)' },
          '100%': { transform: 'translate(0px, 0px) scale(1)' }
        }
      },
      animation: {
        float: 'float 6s ease-in-out infinite',
        blob: 'blob 12s ease-in-out infinite'
      }
    }
  },
  plugins: []
};


