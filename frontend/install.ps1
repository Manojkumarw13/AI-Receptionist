Set-Location ui
Write-Host "Installing base dependencies..."
npm install
Write-Host "Installing 3D and UI dependencies..."
npm install three @types/three @react-three/fiber @react-three/drei gsap framer-motion react-router-dom axios tailwindcss postcss autoprefixer lucide-react clsx tailwind-merge
Write-Host "Initializing Tailwind..."
npx -y tailwindcss init -p
Write-Host "Done."
