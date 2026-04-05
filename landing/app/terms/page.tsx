import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Terms of Service — TCG Scout',
  description: 'Terms of Service for TCG Scout.',
};

export default function TermsPage() {
  return (
    <main style={{ maxWidth: 760, margin: '0 auto', padding: '80px 24px', color: 'var(--text-primary)', fontFamily: 'var(--font-inter), sans-serif' }}>
      <h1 style={{ fontSize: '2rem', fontWeight: 800, marginBottom: 8, letterSpacing: '-0.02em' }}>Terms of Service</h1>
      <p style={{ color: 'var(--text-secondary)', marginBottom: 48, fontSize: '0.9rem' }}>Last updated: April 5, 2026</p>

      <Section title="1. About TCG Scout">
        <p>TCG Scout ("the Service") is operated by TCG Scout ("we", "us", "our"). By accessing or using TCG Scout, including via our Telegram bot (@PokeScoutBot) or website, you agree to these Terms of Service.</p>
        <p>TCG Scout monitors third-party marketplaces (including eBay and TCGPlayer) and sends you Telegram alerts when listings match your saved preferences. We are not a marketplace, seller, or broker. We do not sell, buy, or handle any physical goods.</p>
      </Section>

      <Section title="2. Eligibility">
        <p>You must be at least 18 years old to use TCG Scout. By using the Service you represent that you meet this requirement. You are responsible for ensuring your use of the Service complies with any laws applicable in your jurisdiction.</p>
      </Section>

      <Section title="3. Free Tier and Paid Subscription">
        <p>TCG Scout offers a free tier that includes up to 10 deal alert notifications, with no credit card required. After exhausting your free alerts, continued use of notifications requires an active paid subscription.</p>
        <p>Paid subscriptions are billed monthly at the price displayed at the time of purchase. Pricing may change with reasonable notice. Payments are processed by <strong>Paddle</strong>, our authorised reseller and Merchant of Record. Paddle handles all payment processing, invoicing, and tax compliance — you are contracting with Paddle for the payment transaction itself.</p>
        <p>Your subscription renews automatically each month until cancelled. You may cancel at any time via the bot command <code>/cancel</code> or by contacting us at galbartov17@gmail.com. Cancellation takes effect at the end of the current billing period; no partial refunds are issued for unused time.</p>
      </Section>

      <Section title="4. Refund Policy">
        <p>We offer a 14-day refund window. If you are not satisfied, contact us at galbartov17@gmail.com within 14 days of your payment and we will issue a full refund, no questions asked.</p>
      </Section>

      <Section title="5. Acceptable Use">
        <p>You agree not to:</p>
        <ul>
          <li>Use the Service for any unlawful purpose</li>
          <li>Attempt to reverse-engineer, scrape, or abuse the Service or its underlying systems</li>
          <li>Share your account or subscription with other people</li>
          <li>Use automated tools to interact with the Telegram bot beyond normal use</li>
          <li>Resell or redistribute access to the Service</li>
        </ul>
        <p>We reserve the right to suspend or terminate your access if you violate these terms.</p>
      </Section>

      <Section title="6. No Guarantees on Listings or Deals">
        <p>TCG Scout surfaces listings from third-party platforms. We do not verify, endorse, or guarantee the accuracy, legality, availability, or quality of any listing. Prices, availability, and seller information are pulled from external sources and may be outdated by the time you receive an alert. Always verify a listing on the original marketplace before purchasing.</p>
        <p>We are not responsible for any transactions you enter into with third-party sellers as a result of using the Service.</p>
      </Section>

      <Section title="7. Availability and Uptime">
        <p>We aim to keep TCG Scout running continuously but do not guarantee any specific uptime or availability. The Service may be interrupted for maintenance, updates, or reasons outside our control (including third-party API changes). We are not liable for missed alerts or deals resulting from downtime.</p>
      </Section>

      <Section title="8. Intellectual Property">
        <p>TCG Scout is not affiliated with, endorsed by, or sponsored by Nintendo, The Pokémon Company, Wizards of the Coast, eBay, or TCGPlayer. All trademarks and brand names belong to their respective owners. We use them solely for descriptive purposes.</p>
      </Section>

      <Section title="9. Privacy">
        <p>We collect your Telegram user ID and display name when you start the bot, and we store your saved alert preferences and notification history. We do not sell your data to third parties. Payment data is handled entirely by Paddle — we never see or store your card details.</p>
        <p>By using the Service you consent to this data collection and processing for the purposes of operating the Service.</p>
      </Section>

      <Section title="10. Limitation of Liability">
        <p>To the maximum extent permitted by applicable law, TCG Scout shall not be liable for any indirect, incidental, special, or consequential damages arising from your use of or inability to use the Service, including missed deals, incorrect price data, or third-party marketplace issues. Our total liability to you for any claim arising from these terms or the Service shall not exceed the amount you paid us in the 30 days preceding the claim.</p>
      </Section>

      <Section title="11. Changes to These Terms">
        <p>We may update these Terms of Service from time to time. We will update the "Last updated" date at the top of this page. Continued use of the Service after changes are posted constitutes your acceptance of the updated terms.</p>
      </Section>

      <Section title="12. Governing Law">
        <p>These Terms are governed by and construed in accordance with the laws of the State of Israel, without regard to conflict of law principles. Any disputes arising under these Terms shall be subject to the exclusive jurisdiction of the courts located in Israel.</p>
      </Section>

      <Section title="13. Contact">
        <p>If you have any questions about these Terms, please contact us at:</p>
        <p><strong>Gal Bartov</strong><br />galbartov17@gmail.com</p>
      </Section>
    </main>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section style={{ marginBottom: 40 }}>
      <h2 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: 12, color: 'var(--text-primary)' }}>{title}</h2>
      <div style={{ fontSize: '0.92rem', lineHeight: 1.85, color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: 10 }}>
        {children}
      </div>
    </section>
  );
}
