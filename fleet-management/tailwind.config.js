// tailwind.config.js (for v3)
/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class', // Keep this if you had it, or add it.
  content: [
    "./*.html",             // Scans login.html, dashboard.html
    "./content/**/*.html",  // Scans HTML files in your content folder
    "./js/**/*.js",         // Scans your JavaScript files for class names
  ],
  theme: {
    extend: {
      colors: {
        primary: { // Your custom primary color palette
          light: '#60a5fa', // blue-400
          DEFAULT: '#3b82f6', // blue-500
          dark: '#2563eb',  // blue-600
        },
      },
    },
  },
  plugins: [
    // require('@tailwindcss/forms'), // Example plugin
  ],
}

