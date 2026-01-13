"use client";

export const dynamic = 'force-dynamic';

import { useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useUser } from "../../components/auth/UserContext";

function OAuthSuccessContent() {
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

export default function OAuthSuccessPage() {
  return (
    <Suspense fallback={
      <div className="flex h-screen w-full items-center justify-center">
        <div className="text-sm text-muted-foreground">Loading...</div>
      </div>
    }>
      <OAuthSuccessContent />
    </Suspense>
  );
}