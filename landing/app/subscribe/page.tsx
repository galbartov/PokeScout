'use client';

import { useEffect, useState, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';

const PADDLE_CLIENT_TOKEN = 'live_150105a35d9845302d9c320f338';
const PADDLE_PRICE_ID = 'pri_01knfhz5hksf3xqy1h4dyevt45';

function SubscribeInner() {
  const searchParams = useSearchParams();
  const userId = searchParams.get('user_id') || '';
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const script = document.createElement('script');
    script.src = 'https://cdn.paddle.com/paddle/v2/paddle.js';
    script.async = true;

    script.onload = () => {
      try {
        const Paddle = (window as any).Paddle;
        Paddle.Initialize({
          token: PADDLE_CLIENT_TOKEN,
          eventCallback: (event: any) => {
            if (event.name === 'checkout.completed') {
              window.location.href = '/subscribe/success';
            }
          },
        });

        setLoading(false);

        Paddle.Checkout.open({
          items: [{ priceId: PADDLE_PRICE_ID, quantity: 1 }],
          customData: userId ? { user_id: userId } : undefined,
          settings: {
            displayMode: 'overlay',
            theme: 'dark',
            locale: 'en',
          },
        });
      } catch (e: any) {
        setError(e?.message || 'Failed to load checkout');
      }
    };

    script.onerror = () => setError('Failed to load Paddle.js');

    document.head.appendChild(script);
    return () => {
      if (document.head.contains(script)) document.head.removeChild(script);
    };
  }, [userId]);

  return (
    <main style={{
      minHeight: '100vh',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      background: '#0a0a14',
      fontFamily: 'sans-serif',
      padding: '40px 24px',
    }}>
      <div style={{ textAlign: 'center', maxWidth: 480 }}>
        <div style={{ fontSize: '2rem', marginBottom: 16 }}>⚡</div>
        <h1 style={{ fontSize: '1.6rem', fontWeight: 800, color: '#f0f0f0', marginBottom: 12 }}>
          Upgrade to TCG Scout Pro
        </h1>
        <p style={{ color: '#8888aa', fontSize: '0.95rem', lineHeight: 1.7, marginBottom: 32 }}>
          Unlimited deal alerts for $9.99/month. Cancel anytime.
        </p>
        {error ? (
          <p style={{ color: '#e53238', fontSize: '0.85rem' }}>
            {error} — please try refreshing the page.
          </p>
        ) : loading ? (
          <p style={{ color: '#8888aa', fontSize: '0.85rem', opacity: 0.6 }}>
            Loading checkout…
          </p>
        ) : null}
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
