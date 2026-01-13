"use client";

export const dynamic = 'force-dynamic';

import { useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useUser } from "../../components/auth/UserContext";

export default function OAuthSuccessPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const provider = searchParams.get("provider");

  const { refreshUser } = useUser();

  useEffect(() => {
    const finalizeOAuth = async () => {
      try {
        // Force refresh auth state and user info
        await refreshUser();
      } catch (err) {
        console.error("Failed to refresh user after OAuth:", err);
      } finally {
        // Always land on dashboard, never login
        router.replace("/dashboard");
      }
    };

    finalizeOAuth();
  }, [refreshUser, router]);

  return (
    <div className="flex h-screen w-full items-center justify-center">
      <div className="text-sm text-muted-foreground">
        Finalizing {provider ?? "connection"}…
      </div>
    </div>
  );
}