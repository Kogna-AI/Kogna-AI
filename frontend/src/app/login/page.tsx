"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { LoginScreen } from "../components/auth/LoginPage";
import { useUser } from "../components/auth/UserContext";

export default function LoginPage() {
  const { isAuthenticated, loading } = useUser();
  const router = useRouter();

  useEffect(() => {
    if (loading) return;

    if (isAuthenticated) {
      router.replace("/dashboard");
    }
  }, [loading, isAuthenticated, router]);

  const handleCreateAccount = () => {
    router.push("/signup");
  };

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center text-sm text-muted-foreground">
        Checking authentication…
      </div>
    );
  }

  if (isAuthenticated) {
    return null;
  }

  return <LoginScreen onCreateAccount={handleCreateAccount} />;
}
