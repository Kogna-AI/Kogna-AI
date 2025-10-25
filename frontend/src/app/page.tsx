"use client";
import { UserProvider, useUser } from "./components/auth/UserContext";
import { LandingPage } from "./components/dashboard/LandingPage";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

export default function HomePage() {
  const { isAuthenticated } = useUser();
  const router = useRouter();

  useEffect(() => {
    if (isAuthenticated) {
      router.push('/dashboard');
    }
  }, [isAuthenticated, router]);

  return (
    <UserProvider>
      <LandingPage onGetStarted={() => router.push("/login")} />
    </UserProvider>
  );
}
