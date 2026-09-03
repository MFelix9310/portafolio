import AboutView from '@/components/pages/AboutView';

export const revalidate = 300;

export const metadata = { title: "Sobre mí" };

export default function Page() {
  return <AboutView locale="es" />;
}
