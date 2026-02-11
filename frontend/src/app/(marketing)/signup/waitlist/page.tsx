// frontend/src/app/signup/waitlist/page.tsx
"use client";

import { useRouter } from "next/navigation";
import JoinWaitlistPage from "../../../components/auth/JoinWaitlist";
export default function WaitlistPage() {
  const router = useRouter();

  // Defines what happens when the user clicks "Back" in the component
  const handleBack = () => {
    router.push("/"); // Send them back to the Landing Page
  };

  return (
    <JoinWaitlistPage 
      onBackToLogin={handleBack} 
    />
  );
}