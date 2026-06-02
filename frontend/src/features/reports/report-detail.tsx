"use client";

import { useQuery } from "@tanstack/react-query";
import { Download } from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { useRequireAuth } from "@/hooks/use-require-auth";
import { reportApi } from "@/services/api";

export function ReportDetail({ id }: { id: string }) {
  const ready = useRequireAuth();
  const report = useQuery({ queryKey: ["report", id], queryFn: () => reportApi.get(id), enabled: Boolean(id) });
  const summary = report.data?.summary ?? {};
  const rows = Object.entries(summary).filter(([key]) => key !== "recommendations");
  async function download() {
    const blob = await reportApi.download(id);
    const href = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = href;
    anchor.download = `posture-report-${id}.json`;
    anchor.click();
    URL.revokeObjectURL(href);
  }
  if (!ready) return null;

  return (
    <AppShell>
      <div className="mb-5 flex items-center justify-between">
        <h1 className="text-2xl font-bold">Report</h1>
        <Button onClick={download} disabled={!report.data}><Download className="h-4 w-4" /> Download</Button>
      </div>
      <Card>
        <p className="text-sm text-slate-500">Session</p>
        <p className="mt-1 font-mono text-sm">{report.data?.session_id}</p>
        <div className="mt-5 grid gap-3 md:grid-cols-3">
          {rows.map(([key, value]) => (
            <div key={key} className="rounded-md border border-border p-3">
              <p className="text-sm capitalize text-slate-500">{key.replaceAll("_", " ")}</p>
              <p className="mt-1 text-xl font-bold">{String(value)}</p>
            </div>
          ))}
        </div>
        <div className="mt-5">
          <h2 className="font-semibold">Recommendations</h2>
          <ul className="mt-2 list-disc pl-5 text-sm text-slate-700">
            {Array.isArray(summary.recommendations) && summary.recommendations.map((tip) => <li key={String(tip)}>{String(tip)}</li>)}
          </ul>
        </div>
      </Card>
    </AppShell>
  );
}
