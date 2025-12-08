"use client";
import { LoginScreen } from "../components/auth/LoginPage";
import { useUser } from "../components/auth/UserContext";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

export default function LoginPage() {
  const { isAuthenticated } = useUser();
  const router = useRouter();

  useEffect(() => {
    if (isAuthenticated) {
      router.push('/dashboard');
    }
  }, [isAuthenticated, router]);

  //  ADD THIS - Handle navigation to signup page
  const handleCreateAccount = () => {
    router.push('/signup');
  };

  if (isAuthenticated) {
    return null;
  }

  //  UPDATE THIS - Pass onCreateAccount prop
  return <LoginScreen onCreateAccount={handleCreateAccount} />;
}