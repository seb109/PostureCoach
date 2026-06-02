import { ReportDetail } from "@/features/reports/report-detail";

export default async function ReportPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <ReportDetail id={id} />;
}
