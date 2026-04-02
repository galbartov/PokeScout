'use client';
import { useEffect, useRef } from 'react';

export default function CursorGlow() {
  const glowRef = useRef<HTMLDivElement>(null);
  const dotRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const glow = glowRef.current;
    const dot = dotRef.current;
    if (!glow || !dot) return;

    let rafId: number;
    let mx = -999, my = -999;
    // Spring state for the large glow (lags more)
    let gx = -999, gy = -999;

    const onMove = (e: MouseEvent) => {
      mx = e.clientX;
      my = e.clientY;
      // Dot follows instantly
      dot.style.transform = `translate(${mx}px, ${my}px)`;
    };

    const SPRING = 0.06;

    const tick = () => {
      gx += (mx - gx) * SPRING;
      gy += (my - gy) * SPRING;
      glow.style.transform = `translate(${gx}px, ${gy}px)`;
      rafId = requestAnimationFrame(tick);
    };

    window.addEventListener('mousemove', onMove, { passive: true });
    rafId = requestAnimationFrame(tick);
    return () => {
      window.removeEventListener('mousemove', onMove);
      cancelAnimationFrame(rafId);
    };
  }, []);

  return (
    <>
      {/* Large lagging spotlight */}
      <div
        ref={glowRef}
        style={{
          position: 'fixed',
          top: 0, left: 0,
          width: 700, height: 700,
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(245,183,49,0.035) 0%, transparent 60%)',
          pointerEvents: 'none',
          zIndex: 9998,
          willChange: 'transform',
          translate: '-50% -50%',
          mixBlendMode: 'screen',
        }}
      />
      {/* Small precise dot */}
      <div
        ref={dotRef}
        style={{
          position: 'fixed',
          top: 0, left: 0,
          width: 6, height: 6,
          borderRadius: '50%',
          background: 'rgba(245,183,49,0.7)',
          pointerEvents: 'none',
          zIndex: 9999,
          willChange: 'transform',
          translate: '-50% -50%',
          boxShadow: '0 0 10px rgba(245,183,49,0.5)',
          mixBlendMode: 'screen',
        }}
      />
    </>
  );
}
