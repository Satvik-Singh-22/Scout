import nextDynamic from 'next/dynamic';

export const dynamic = 'force-dynamic';

const LandingPage = nextDynamic(() => import('@/components/LandingPage'), {
  ssr: false,
});

export default function Page() {
  return <LandingPage />;
}