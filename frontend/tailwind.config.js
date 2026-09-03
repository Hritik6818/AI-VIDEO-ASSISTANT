/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        ink: '#14161C',
        surface: '#1B1E27',
        surfaceAlt: '#21242F',
        line: '#2C303C',
        text: '#EDEEF0',
        muted: '#9096A8',
        amber: '#E8A33D',
        amberDim: '#B87F2C',
        teal: '#4FB8A6',
        coral: '#E2665A',
      },
      fontFamily: {
        display: ['"Fraunces"', 'serif'],
        body: ['"Inter"', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
