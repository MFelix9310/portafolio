import AboutView from '@/components/pages/AboutView';

export const revalidate = 300;

export const metadata = { title: "About" };

export default function Page() {
  return <AboutView locale="en" />;
}
