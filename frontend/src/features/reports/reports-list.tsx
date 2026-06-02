"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { AppShell } from "@/components/app-shell";
import { Card } from "@/components/ui/card";
import { useRequireAuth } from "@/hooks/use-require-auth";
import { reportApi } from "@/services/api";

export function ReportsList() {
  const ready = useRequireAuth();
  const reports = useQuery({ queryKey: ["reports"], queryFn: reportApi.list });

  if (!ready) return null;

  return (
    <AppShell>
      <div className="mb-5">
        <h1 className="text-2xl font-bold">Reports</h1>
        <p className="text-sm text-slate-600">Generated posture summaries</p>
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        {reports.data?.map((report) => (
          <Link key={report.id} href={`/reports/${report.id}` as never}>
            <Card className="transition hover:border-primary">
              <p className="font-semibold">{new Date(report.generated_at).toLocaleString()}</p>
              <p className="mt-1 text-sm text-slate-600">Session {report.session_id}</p>
              <p className="mt-3 text-2xl font-bold">{String(report.summary.average_score ?? 0)}</p>
            </Card>
          </Link>
        ))}
        {reports.data?.length === 0 && <Card>No reports yet.</Card>}
      </div>
    </AppShell>
  );
}
