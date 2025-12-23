/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    darkMode: 'class',
    theme: {
        extend: {
            colors: {
                // Dark theme palette
                surface: {
                    DEFAULT: 'rgba(20, 20, 30, 0.8)',
                    solid: '#14141e',
                },
                accent: {
                    primary: '#208296',
                    secondary: '#6366f1',
                },
                success: '#22c55e',
                warning: '#f59e0b',
                danger: '#ef4444',
            },
            backdropBlur: {
                xs: '2px',
            },
            animation: {
                'float': 'float 6s ease-in-out infinite',
                'pulse-slow': 'pulse 3s ease-in-out infinite',
            },
            keyframes: {
                float: {
                    '0%, 100%': { transform: 'translateY(0)' },
                    '50%': { transform: 'translateY(-10px)' },
                },
            },
        },
    },
    plugins: [],
}
