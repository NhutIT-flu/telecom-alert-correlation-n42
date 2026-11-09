/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        noc: {
          bg: '#0a0e17',        // Nền chính
          surface: '#121826',   // Nền card/panel
          border: '#1e293b',    // Đường viền
          critical: '#ef4444',  // Severity 0-2 (Đỏ)
          major: '#f97316',     // Severity 3 (Cam)
          minor: '#f59e0b',     // Severity 4 (Vàng)
          info: '#06b6d4',      // Severity 5-6 (Cyan)
        },
      },
    },
  },
  plugins: [],
}