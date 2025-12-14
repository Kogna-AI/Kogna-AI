"use client";

import { useRouter } from "next/navigation";
import CreateAccountPage from "../components/auth/CreateAccountPage";

export default function SignupPage() {
  const router = useRouter();

  const handleBackToLogin = () => {
    router.push("/login");
  };

  return <CreateAccountPage onBackToLogin={handleBackToLogin} />;
}