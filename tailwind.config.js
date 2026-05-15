/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html",
    "./**/templates/**/*.html",
    "./static/js/**/*.js",
    // ajoute d’autres chemins où tu utilises Tailwind (JS, JSX, etc.)
  ],
  theme: {
    extend: {},
  },
  safelist: [
    // Ajoute ici toutes les classes dynamiques ou les variantes que tu veux conserver
    'bg-red-500',
    'bg-green-500',
    'bg-blue-500',
    'text-red-500',
    'hover:bg-indigo-900',
    // etc. selon tes besoins
  ],
  plugins: [],
}
