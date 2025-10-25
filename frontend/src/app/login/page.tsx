"use client";
import { LoginScreen } from "../components/auth/LoginPage";
import { useUser } from "../components/auth/UserContext";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

export default function LoginPage() {
  const { isAuthenticated } = useUser();
  const router = useRouter();

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      router.push('/dashboard');
    }
  }, [isAuthenticated, router]);

  if (isAuthenticated) {
    return null; // Will redirect to dashboard
  }

  return <LoginScreen />;
}
