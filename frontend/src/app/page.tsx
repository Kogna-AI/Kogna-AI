// frontend/src/app/page.tsx
"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useUser } from "./components/auth/UserContext";
import { LandingPage } from "./components/LandingPage";

export default function RootPage() {
  const { isAuthenticated, loading } = useUser();
  const router = useRouter();
  const [isClient, setIsClient] = useState(false);

  useEffect(() => {
    setIsClient(true);
    // Only redirect if they are ALREADY logged in
    if (!loading && isAuthenticated) {
      router.replace("/dashboard");
    }
  }, [loading, isAuthenticated, router]);

  // Handlers for the Landing Page buttons
  const handleJoinWaitlist = () => router.push("/signup/waitlist");
  const handleGetStarted = () => router.push("/signup");
  const handleLogin = () => router.push("/login");

  // While checking auth status, you might want to show a spinner or nothing
  // But for a public landing page, we usually render the page and redirect *only* if auth is confirmed
  if (loading) return null; 

  // If user is logged in, useEffect handles redirect. 
  // If not logged in, show Landing Page.
  return (
    <LandingPage 
      onJoinWaitlist={handleJoinWaitlist}
      onGetStarted={handleGetStarted} 
      onLogin={handleLogin} 
    />
  );
}