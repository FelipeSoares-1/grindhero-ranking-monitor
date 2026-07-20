import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { fileURLToPath } from 'node:url'

// Build multi-página:
//  - index.html  → monitor completo (com senha)
//  - farm.html   → widget público "Top Farmers do Dia" (embed no redskull.space)
// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  build: {
    rollupOptions: {
      input: {
        main: fileURLToPath(new URL('./index.html', import.meta.url)),
        farm: fileURLToPath(new URL('./farm.html', import.meta.url)),
      },
    },
  },
})
