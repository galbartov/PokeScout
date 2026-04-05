'use client';

import { useEffect, useSearchParams } from 'next/navigation';
import { Suspense } from 'react';

const PADDLE_CLIENT_TOKEN = 'live_150105a35d9845302d9c320f338';
const PADDLE_PRICE_ID = 'pri_01knfhz5hksf3xqy1h4dyevt45';

function SubscribeInner() {
  const searchParams = useSearchParams();
  const userId = searchParams.get('user_id') || '';

  useEffect(() => {
    // Dynamically load Paddle.js
    const script = document.createElement('script');
    script.src = 'https://cdn.paddle.com/paddle/v2/paddle.js';
    script.async = true;
    script.onload = () => {
      const Paddle = (window as any).Paddle;
      Paddle.Environment.set('production');
      Paddle.Initialize({
        token: PADDLE_CLIENT_TOKEN,
        eventCallback: (event: any) => {
          if (event.name === 'checkout.completed') {
            window.location.href = '/subscribe/success';
          }
        },
      });

      Paddle.Checkout.open({
        items: [{ priceId: PADDLE_PRICE_ID, quantity: 1 }],
        customData: { user_id: userId },
        settings: {
          displayMode: 'overlay',
          theme: 'dark',
          locale: 'en',
        },
      });
    };
    document.head.appendChild(script);

    return () => {
      document.head.removeChild(script);
    };
  }, [userId]);

  return (
    <main style={{
      minHeight: '100vh',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'var(--bg-deep)',
      fontFamily: 'var(--font-inter), sans-serif',
      padding: '40px 24px',
    }}>
      <div style={{ textAlign: 'center', maxWidth: 480 }}>
        <div style={{ fontSize: '2rem', marginBottom: 16 }}>⚡</div>
        <h1 style={{ fontSize: '1.6rem', fontWeight: 800, color: 'var(--text-primary)', marginBottom: 12, letterSpacing: '-0.02em' }}>
          Upgrade to TCG Scout Pro
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem', lineHeight: 1.7, marginBottom: 32 }}>
          Unlimited deal alerts for $9.99/month. Cancel anytime.
        </p>
        <div style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', opacity: 0.6 }}>
          Loading checkout…
        </div>
      </div>
    </main>
  );
}

export default function SubscribePage() {
  return (
    <Suspense>
      <SubscribeInner />
    </Suspense>
  );
}
