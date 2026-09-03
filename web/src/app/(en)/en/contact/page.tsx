import ContactView from '@/components/pages/ContactView';

export const revalidate = 300;

export const metadata = { title: "Contact" };

export default function Page() {
  return <ContactView locale="en" />;
}
