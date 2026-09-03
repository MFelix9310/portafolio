import AreaView from '@/components/pages/AreaView';

export const revalidate = 300;

export const metadata = { title: "Data" };

export default function Page() {
  return <AreaView areaKey="data" locale="en" />;
}
