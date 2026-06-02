"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { authApi } from "@/services/api";
import { setTokens } from "@/store/auth";

export function AuthForm({ mode }: { mode: "login" | "register" }) {
  const router = useRouter();
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError("");
    const form = new FormData(event.currentTarget);
    try {
      const tokens = mode === "login"
        ? await authApi.login({ email: String(form.get("email")), password: String(form.get("password")) })
        : await authApi.register({ email: String(form.get("email")), full_name: String(form.get("full_name")), password: String(form.get("password")) });
      setTokens(tokens);
      router.push("/dashboard");
    } catch {
      setError("Authentication failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      <Card className="w-full max-w-md">
        <h1 className="text-2xl font-bold">{mode === "login" ? "Sign in" : "Create account"}</h1>
        <form onSubmit={submit} className="mt-5 space-y-3">
          {mode === "register" && <Input name="full_name" placeholder="Full name" required minLength={2} />}
          <Input name="email" type="email" placeholder="Email" required />
          <Input name="password" type="password" placeholder="Password" required minLength={8} />
          {error && <p className="text-sm text-red-600">{error}</p>}
          <Button disabled={loading} className="w-full">{loading ? "Working..." : mode === "login" ? "Login" : "Register"}</Button>
        </form>
        <Link href={mode === "login" ? "/register" : "/login"} className="mt-4 block text-sm text-primary">
          {mode === "login" ? "Create a new account" : "Use an existing account"}
        </Link>
      </Card>
    </div>
  );
}
