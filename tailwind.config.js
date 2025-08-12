/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/templates/**/*.html", // IntelliSense가 감시할 파일 경로
  ],
  plugins: [
    require('./app/static/js/daisyui.js')
  ],
}