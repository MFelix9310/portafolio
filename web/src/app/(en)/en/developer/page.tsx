import AreaView from '@/components/pages/AreaView';

export const revalidate = 300;

export const metadata = { title: "Development" };

export default function Page() {
  return <AreaView areaKey="developer" locale="en" />;
}
