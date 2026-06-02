"use client";

import { useQuery } from "@tanstack/react-query";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import Link from "next/link";
import { AppShell } from "@/components/app-shell";
import { Card } from "@/components/ui/card";
import { reportApi, sessionApi, userApi } from "@/services/api";
import { useRequireAuth } from "@/hooks/use-require-auth";

export function Dashboard() {
  const ready = useRequireAuth();
  const user = useQuery({ queryKey: ["me"], queryFn: userApi.me });
  const sessions = useQuery({ queryKey: ["sessions"], queryFn: sessionApi.list });
  const stats = useQuery({ queryKey: ["stats"], queryFn: sessionApi.stats });
  const reports = useQuery({ queryKey: ["reports"], queryFn: reportApi.list });
  const chart = [
    { name: "Good", value: stats.data?.good_percentage ?? 0 },
    { name: "Slight", value: stats.data?.slight_percentage ?? 0 },
    { name: "Bad", value: stats.data?.bad_percentage ?? 0 }
  ];

  if (!ready) return null;

  return (
    <AppShell>
      <div className="mb-6">
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <p className="text-sm text-slate-600">{user.data?.full_name ?? "PostureCoach user"}</p>
      </div>
      <div className="grid gap-4 md:grid-cols-4">
        <Card><p className="text-sm text-slate-500">Sessions</p><p className="mt-2 text-3xl font-bold">{stats.data?.total_sessions ?? 0}</p></Card>
        <Card><p className="text-sm text-slate-500">Minutes</p><p className="mt-2 text-3xl font-bold">{stats.data?.total_minutes ?? 0}</p></Card>
        <Card><p className="text-sm text-slate-500">Average score</p><p className="mt-2 text-3xl font-bold">{stats.data?.average_score ?? 0}</p></Card>
        <Card><p className="text-sm text-slate-500">Reports</p><p className="mt-2 text-3xl font-bold">{reports.data?.length ?? 0}</p></Card>
      </div>
      <div className="mt-6 grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <h2 className="mb-4 font-semibold">Posture distribution</h2>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chart}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="name" /><YAxis /><Tooltip /><Bar dataKey="value" fill="#278b82" radius={[4, 4, 0, 0]} /></BarChart>
            </ResponsiveContainer>
          </div>
        </Card>
        <Card>
          <h2 className="mb-4 font-semibold">Session history</h2>
          <div className="space-y-3">
            {sessions.data?.map((session) => (
              <Link key={session.id} href={(session.report_id ? `/reports/${session.report_id}` : `/monitor?session=${session.id}`) as never} className="block rounded-md border border-border p-3">
                <p className="font-medium">{new Date(session.started_at).toLocaleString()}</p>
                <p className="text-sm text-slate-600">Score {session.average_score} • {session.status}</p>
              </Link>
            ))}
          </div>
        </Card>
      </div>
    </AppShell>
  );
}
