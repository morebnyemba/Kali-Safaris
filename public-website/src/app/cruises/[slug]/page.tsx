import { notFound } from "next/navigation";
import CruiseDetail from "@/components/CruiseDetail";
import FooterSection from "@/components/FooterSection";
import { CRUISES } from "@/lib/cruises";
import { pageMetadata } from "@/lib/seo";

export const dynamicParams = false;

export function generateStaticParams() {
  return CRUISES.map(({ slug }) => ({ slug }));
}

export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const cruise = CRUISES.find((c) => c.slug === slug);
  if (!cruise) return {};
  return pageMetadata(cruise.title, `${cruise.description} Book online above Victoria Falls.`, `/cruises/${cruise.slug}`);
}

export default async function CruisePage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const cruise = CRUISES.find((c) => c.slug === slug);
  if (!cruise) notFound();
  return (
    <div className="flex min-h-screen flex-col">
      <CruiseDetail cruise={cruise} />
      <FooterSection />
    </div>
  );
}
