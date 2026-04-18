import nextDynamic from 'next/dynamic';

const LandingPage = nextDynamic(() => import('@/components/LandingPage'), {
  ssr: false,
  loading: () => null,
});

export default function Page() {
  return <LandingPage />;
}