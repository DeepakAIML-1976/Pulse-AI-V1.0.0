/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx}",
    "./components/**/*.{js,ts,jsx,tsx}",
    "./pages/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'pulse-blue': '#4F46E5',
        'pulse-purple': '#7C3AED',
        'pulse-gray': '#E5E7EB',
      },
    },
  },
  plugins: [],
};
