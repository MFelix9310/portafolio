import ContactView from '@/components/pages/ContactView';

export const revalidate = 300;

export const metadata = { title: "Contacto" };

export default function Page() {
  return <ContactView locale="es" />;
}
