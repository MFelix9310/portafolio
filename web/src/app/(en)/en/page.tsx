import HomeView from '@/components/pages/HomeView';

export const revalidate = 300;

export const metadata = { title: "Félix Ruiz M. — Portfolio" };

export default function Page() {
  return <HomeView locale="en" />;
}
