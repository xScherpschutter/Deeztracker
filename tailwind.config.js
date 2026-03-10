/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: '#00AAFF',
        background: '#121212',
        surface: '#1E1E1E',
        textWhite: '#FFFFFF',
        textGray: '#9CA3AF',
      },
    },
  },
  plugins: [],
}
