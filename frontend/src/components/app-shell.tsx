"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { Activity, BarChart3, Camera, FileText, LogOut } from "lucide-react";
import { Button } from "@/components/ui/button";
import { clearTokens, getRefreshToken } from "@/store/auth";
import { authApi } from "@/services/api";

const nav = [
  { href: "/dashboard", label: "Dashboard", icon: BarChart3 },
  { href: "/monitor", label: "Monitor", icon: Camera },
  { href: "/reports", label: "Reports", icon: FileText }
] as const;

export function AppShell({ children }: { children: React.ReactNode }) {
  const path = usePathname();
  const router = useRouter();
  async function logout() {
    const token = getRefreshToken();
    if (token) await authApi.logout(token).catch(() => undefined);
    clearTokens();
    router.push("/login");
  }
  return (
    <div className="min-h-screen">
      <header className="border-b border-border bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3">
          <Link href="/dashboard" className="flex items-center gap-2 font-bold">
            <Activity className="h-5 w-5 text-primary" /> PostureCoach
          </Link>
          <nav className="flex items-center gap-2">
            {nav.map((item) => (
              <Link key={item.href} href={item.href as never} className={`flex items-center gap-2 rounded-md px-3 py-2 text-sm ${path === item.href ? "bg-muted font-semibold" : "hover:bg-muted"}`}>
                <item.icon className="h-4 w-4" /> {item.label}
              </Link>
            ))}
            <Button onClick={logout} className="bg-slate-900"><LogOut className="h-4 w-4" /> Logout</Button>
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-4 py-6">{children}</main>
    </div>
  );
}
