"use client";
import { UserProvider, useUser } from "./components/auth/UserContext";
import { LandingPage } from "./components/dashboard/LandingPage";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { DataConnectorHub } from "./components/dashboard/DataConnectorHub";
import AppContent from "./App";

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
      {process.env.NEXT_PUBLIC_DEV_AUTH === "true" ? (
        <AppContent></AppContent>
      ) : (
        <LandingPage onGetStarted={() => router.push("/login")} />
      )}
      
    </UserProvider>
  );
}
