"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { LayoutShell } from "@/components/layout-shell";
import { SectionCard } from "@/components/section-card";
import { apiRequest } from "@/lib/api";
import { loadSession, saveSession } from "@/lib/auth";
import type { TokenResponse } from "@/types";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("admin@example.com");
  const [password, setPassword] = useState("admin123");
  const [session, setSession] = useState<TokenResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setSession(loadSession());
  }, []);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const payload = await apiRequest<TokenResponse>("/auth/login", {
        method: "POST",
        body: { email, password },
      });
      saveSession(payload);
      setSession(payload);
      router.push("/dashboard");
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "Unable to sign in.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <LayoutShell
      title="Login"
      description="Use the backend JWT endpoint to create a browser session for the protected dashboard, review, and admin pages."
    >
      <div className="grid grid--two">
        <SectionCard title="Sign In">
          <form className="form" onSubmit={handleSubmit}>
            <label className="field">
              <span>Email</span>
              <input value={email} onChange={(event) => setEmail(event.target.value)} type="email" />
            </label>
            <label className="field">
              <span>Password</span>
              <input value={password} onChange={(event) => setPassword(event.target.value)} type="password" />
            </label>
            {error ? <p className="error-text">{error}</p> : null}
            <button className="button" disabled={loading} type="submit">
              {loading ? "Signing In..." : "Sign In"}
            </button>
          </form>
        </SectionCard>

        <SectionCard title="Current Session">
          {session ? (
            <>
              <p>
                Signed in as <strong>{session.user.full_name}</strong> ({session.user.role}).
              </p>
              <p className="muted">The access token is stored in local browser storage for this demo UI.</p>
              <Link className="button" href="/dashboard">
                Open Dashboard
              </Link>
            </>
          ) : (
            <>
              <p>No session is stored yet.</p>
              <p className="muted">
                Default local credentials are prefilled for the bootstrapped admin user created by the backend.
              </p>
            </>
          )}
        </SectionCard>
      </div>
    </LayoutShell>
  );
}
