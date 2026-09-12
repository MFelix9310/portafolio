import HomeView from '@/components/pages/HomeView';

export const revalidate = 300;

// Sin `absolute`, la plantilla del layout le anade otra vez el sufijo y sale
// «Félix Ruiz M. — Portfolio · Félix Ruiz M.» en la home inglesa.
export const metadata = { title: { absolute: 'Félix Ruiz M. — Portfolio' } };

export default function Page() {
  return <HomeView locale="en" />;
}
