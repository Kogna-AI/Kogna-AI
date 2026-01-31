"use client";

import { useEffect, useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import CreateAccountPage from "@/app/components/auth/CreateAccountPage";
import { Card, CardContent } from "@/app/ui/card";
import { Loader2, AlertCircle } from "lucide-react";
import { Button } from "@/app/ui/button";

export default function VerifySignupPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const [status, setStatus] = useState<"loading" | "verified" | "error">("loading");
  const [email, setEmail] = useState("");
  const [error, setError] = useState("");
  const [token, setToken] = useState("");

  useEffect(() => {
    const verifyToken = async () => {
      const urlToken = searchParams.get("token");

      if (!urlToken) {
        setStatus("error");
        setError("Invalid verification link");
        return;
      }

      setToken(urlToken);

      try {
        const response = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/api/auth/verify-signup-token?token=${urlToken}`
        );

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || "Verification failed");
        }

        const data = await response.json();
        setEmail(data.email);
        setStatus("verified");
      } catch (err: any) {
        setStatus("error");
        setError(err.message || "Verification failed");
      }
    };

    verifyToken();
  }, [searchParams]);

  if (status === "loading") {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center p-4">
        <Card className="w-full max-w-md shadow-xl border-0">
          <CardContent className="pt-8 pb-8 text-center">
            <Loader2 className="w-12 h-12 text-indigo-600 animate-spin mx-auto mb-4" />
            <p className="text-muted-foreground">Verifying your email...</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (status === "error") {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center p-4">
        <Card className="w-full max-w-md shadow-xl border-0">
          <CardContent className="pt-8 pb-8 text-center space-y-4">
            <div className="w-16 h-16 mx-auto rounded-full bg-red-100 flex items-center justify-center">
              <AlertCircle className="w-10 h-10 text-red-600" />
            </div>
            <div className="space-y-2">
              <h2 className="text-2xl font-bold">Verification Failed</h2>
              <p className="text-muted-foreground">{error}</p>
            </div>
            <Button onClick={() => router.push("/signup")} className="w-full">
              Request New Link
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <CreateAccountPage
      onBackToLogin={() => router.push("/login")}
      initialRole="founder"
      lockRole={false}
      verifiedEmail={email}
      signupToken={token}
    />
  );
}