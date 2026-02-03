"use client";
import { useRouter } from "next/navigation";
import { LoginScreen } from "../components/auth/LoginPage";

export default function LoginPage() {
  const router = useRouter();

  const handleCreateAccount = () => {
    router.push("/signup/waitlist");  // Changed from "/signup"
  };

  return <LoginScreen onCreateAccount={handleCreateAccount} />;
}
