"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useUser } from "./components/auth/UserContext";

export default function RootPage() {
  const { isAuthenticated, loading } = useUser();
  const router = useRouter();

  useEffect(() => {
    if (loading) return;

    if (isAuthenticated) {
      router.replace("/dashboard");
    } else {
      router.replace("/login");
    }
  }, [loading, isAuthenticated, router]);

  return (
    <div className="flex h-screen items-center justify-center text-sm text-muted-foreground">
      Redirecting…
    </div>
  );
}
