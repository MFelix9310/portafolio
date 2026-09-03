import CivilBimView from '@/components/pages/CivilBimView';

export const revalidate = 300;

export const metadata = { title: "Civil & BIM" };

export default function Page() {
  return <CivilBimView locale="en" />;
}
