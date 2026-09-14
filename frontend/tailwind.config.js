/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        app: {
          bg: '#0d0f12',
          surface: '#1c1e23',
          'surface-hover': '#24272e',
          sheet: '#1e2025',
          btn: '#2a2d35',
          'btn-hover': '#333742',
          accent: '#2196f3',
          'accent-hover': '#1e88e5',
        }
      },
      fontFamily: {
        sans: ['"Outfit"', '"Noto Sans JP"', '-apple-system', 'BlinkMacSystemFont', '"Segoe UI"', 'sans-serif'],
      }
    },
  },
  plugins: [],
}

