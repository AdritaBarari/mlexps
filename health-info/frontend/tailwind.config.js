/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        bg: {
          primary: '#0D1117',
          card: '#161B22',
          elevated: '#21262D',
        },
        accent: {
          DEFAULT: '#00D4AA',
          warn: '#F0A500',
          danger: '#F85149',
        },
        text: {
          primary: '#E6EDF3',
          muted: '#8B949E',
        },
        border: '#30363D',
      },
      fontFamily: {
        body: ['Inter', 'sans-serif'],
        heading: ['Sora', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
