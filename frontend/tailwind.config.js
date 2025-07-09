/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx,html}",  // Adjust if your source files are elsewhere
    "./public/index.html"               // Add this if you have a static html file
  ],
  theme: {
    extend: {
      // Add custom colors, fonts, spacing here if you want
    },
  },
  plugins: [],
};
