/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Adding a custom "Slate-950" for that high-tech dark mode aesthetic
        brand: "#0f172a", 
      },
    },
  },
  plugins: [],
}