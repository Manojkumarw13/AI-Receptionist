import React, { useRef } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { Environment, Sphere, MeshDistortMaterial, Float } from '@react-three/drei';

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
        <Sphere ref={orb1Ref} args={[1.5, 64, 64]} position={[-3, 0, -5]}>
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
        <Sphere ref={orb2Ref} args={[2, 64, 64]} position={[3, 0, -8]}>
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

const ThreeBackground = () => {
  return (
    <div className="absolute inset-0 z-0 bg-darker pointer-events-none">
      <Canvas camera={{ position: [0, 0, 5], fov: 75 }}>
        <ambientLight intensity={0.5} />
        <directionalLight position={[10, 10, 5]} intensity={1} color="#ffffff" />
        <directionalLight position={[-10, -10, -5]} intensity={0.5} color="#1392ec" />
        <AnimatedOrbs />
        <Environment preset="city" />
      </Canvas>
      {/* Decorative Blur Overlays for increased depth and premium feel */}
      <div className="absolute inset-0 z-10 bg-gradient-to-br from-darker/60 via-transparent to-darker/80 backdrop-blur-[20px]" />
    </div>
  );
};

export default ThreeBackground;
