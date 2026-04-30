import React, { useRef, Component } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { Sphere, MeshDistortMaterial, Float } from '@react-three/drei';

function AnimatedOrbs() {
  const orb1Ref = useRef();
  const orb2Ref = useRef();

  useFrame((state) => {
    const time = state.clock.getElapsedTime();
    if (orb1Ref.current) {
        orb1Ref.current.position.y = Math.sin(time * 0.5) * 1.5;
        orb1Ref.current.position.x = Math.cos(time * 0.3) * 2 - 3;
    }
    if (orb2Ref.current) {
        orb2Ref.current.position.y = Math.cos(time * 0.4) * 2;
        orb2Ref.current.position.x = Math.sin(time * 0.6) * 3 + 3;
    }
  });

  return (
    <>
      <Float speed={2} rotationIntensity={1} floatIntensity={2}>
        <Sphere ref={orb1Ref} args={[1.5, 32, 32]} position={[-3, 0, -5]}>
          <MeshDistortMaterial 
            color="#1392ec" 
            attach="material" 
            distort={0.4} 
            speed={2} 
            roughness={0.2} 
            metalness={0.8} 
            opacity={0.8} 
            transparent 
          />
        </Sphere>
      </Float>

      <Float speed={3} rotationIntensity={1.5} floatIntensity={1.5}>
        <Sphere ref={orb2Ref} args={[2, 32, 32]} position={[3, 0, -8]}>
          <MeshDistortMaterial 
            color="#60a5fa" 
            attach="material" 
            distort={0.5} 
            speed={1.5} 
            roughness={0.1} 
            metalness={0.5} 
            opacity={0.6} 
            transparent 
          />
        </Sphere>
      </Float>
    </>
  );
}

// Bug E FIX: CSS gradient fallback used when WebGL context is lost or
// the Three.js Canvas crashes. Without this, the background goes blank.
function CSSFallbackBackground() {
  return (
    <div className="absolute inset-0 z-0 bg-darker">
      <div className="absolute inset-0 bg-gradient-to-br from-blue-900/20 via-transparent to-cyan-900/10" />
      <div className="absolute top-1/4 left-1/4 w-64 h-64 bg-blue-500/10 rounded-full blur-[100px] animate-pulse" />
      <div className="absolute bottom-1/3 right-1/4 w-80 h-80 bg-cyan-500/8 rounded-full blur-[120px] animate-pulse" style={{ animationDelay: '1s' }} />
    </div>
  );
}

// Bug E FIX: Error boundary catches WebGL/Three.js crashes and falls back
// to a CSS gradient so the app remains usable.
class WebGLErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error, info) {
    console.warn('WebGL/Three.js crashed, falling back to CSS background:', error.message);
  }

  render() {
    if (this.state.hasError) {
      return <CSSFallbackBackground />;
    }
    return this.props.children;
  }
}

const ThreeBackground = () => {
  return (
    <div className="absolute inset-0 z-0 bg-darker pointer-events-none">
      <WebGLErrorBoundary>
        <Canvas
          camera={{ position: [0, 0, 5], fov: 75 }}
          onCreated={({ gl }) => {
            // Bug E FIX: Listen for WebGL context loss and attempt recovery
            const canvas = gl.domElement;
            canvas.addEventListener('webglcontextlost', (e) => {
              e.preventDefault();
              console.warn('WebGL context lost, will attempt restore...');
            });
            canvas.addEventListener('webglcontextrestored', () => {
              console.info('WebGL context restored.');
            });
          }}
        >
          <ambientLight intensity={0.5} />
          <directionalLight position={[10, 10, 5]} intensity={1} color="#ffffff" />
          <directionalLight position={[-10, -10, -5]} intensity={0.5} color="#1392ec" />
          <AnimatedOrbs />
        </Canvas>
      </WebGLErrorBoundary>
      {/* Decorative Blur Overlays for increased depth and premium feel */}
      <div className="absolute inset-0 z-10 bg-gradient-to-br from-darker/60 via-transparent to-darker/80 backdrop-blur-[20px]" />
    </div>
  );
};

export default ThreeBackground;
