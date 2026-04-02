'use client';
import { strings } from '@/lib/i18n';
import { useEffect, useRef } from 'react';

export default function FAQ() {
  const ref = useRef<HTMLElement>(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => entries.forEach(e => e.target.classList.toggle('visible', e.isIntersecting)),
      { threshold: 0.1 }
    );
    ref.current?.querySelectorAll('.reveal').forEach(el => observer.observe(el));
    return () => observer.disconnect();
  }, []);

  return (
    <section ref={ref} className="section-pad" style={{ background: 'var(--bg-deep)' }}>
      <div style={{ maxWidth: 720, margin: '0 auto' }}>
        <h2 className="reveal" style={{
          fontSize: 'clamp(1.8rem, 3vw, 2.8rem)',
          textAlign: 'center',
          marginBottom: 64,
          letterSpacing: '-0.02em',
        }}>
          {strings.faq.title}
        </h2>

        <div className="reveal" style={{
          background: 'var(--bg-surface)',
          border: '1px solid var(--border)',
          borderRadius: 20,
          overflow: 'hidden',
        }}>
          {strings.faq.items.map((item, i) => (
            <details key={i} style={{ borderBottom: i < strings.faq.items.length - 1 ? '1px solid var(--border)' : 'none' }}>
              <summary>{item.q}</summary>
              <div className="faq-body">{item.a}</div>
            </details>
          ))}
        </div>
      </div>
    </section>
  );
}
