"use client";
import { useEffect, useState, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { Card, CardContent } from "@/app/ui/card";
import { Button } from "@/app/ui/button";
import { CheckCircle2, AlertCircle, Loader2 } from "lucide-react";
import api from "@/services/api";

function VerifyEmailContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const [status, setStatus] = useState<"loading" | "success" | "error">("loading");
  const [message, setMessage] = useState("");

  useEffect(() => {
    const verifyEmail = async () => {
      const token = searchParams.get("token");
      if (!token) {
        setStatus("error");
        setMessage("Invalid verification link. No token provided.");
        return;
      }
      try {
        const data = await api.verifyEmail(token);
        setStatus("success");
        setMessage(data.message || "Email verified successfully!");
        setTimeout(() => {
          router.push("/login");
        }, 3000);
      } catch (error: any) {
        setStatus("error");
        setMessage(error.message || "Verification failed");
      }
    };
    verifyEmail();
  }, [searchParams, router]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center p-4">
      <Card className="w-full max-w-md shadow-xl border-0">
        <CardContent className="pt-8 pb-8">
          {status === "loading" && (
            <div className="text-center space-y-4">
              <Loader2 className="w-12 h-12 text-indigo-600 animate-spin mx-auto" />
              <div className="space-y-2">
                <h2 className="text-xl font-semibold">Verifying your email...</h2>
                <p className="text-sm text-muted-foreground">
                  Please wait while we verify your email address.
                </p>
              </div>
            </div>
          )}
          {status === "success" && (
            <div className="text-center space-y-4">
              <div className="w-16 h-16 mx-auto rounded-full bg-green-100 flex items-center justify-center">
                <CheckCircle2 className="w-10 h-10 text-green-600" />
              </div>
              <div className="space-y-2">
                <h2 className="text-2xl font-bold">Email Verified! 🎉</h2>
                <p className="text-muted-foreground">{message}</p>
              </div>
              <div className="flex items-center justify-center gap-2 text-sm text-muted-foreground mt-4">
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Redirecting to login...</span>
              </div>
            </div>
          )}
          {status === "error" && (
            <div className="text-center space-y-4">
              <div className="w-16 h-16 mx-auto rounded-full bg-red-100 flex items-center justify-center">
                <AlertCircle className="w-10 h-10 text-red-600" />
              </div>
              <div className="space-y-2">
                <h2 className="text-2xl font-bold">Verification Failed</h2>
                <p className="text-muted-foreground">{message}</p>
              </div>
              <Button
                onClick={() => router.push("/login")}
                className="w-full mt-4"
              >
                Go to Login
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default function VerifyEmailPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center p-4">
          <Card className="w-full max-w-md shadow-xl border-0">
            <CardContent className="pt-8 pb-8 text-center">
              <Loader2 className="w-12 h-12 text-indigo-600 animate-spin mx-auto mb-4" />
              <p className="text-muted-foreground">Loading...</p>
            </CardContent>
          </Card>
        </div>
      }
    >
      <VerifyEmailContent />
    </Suspense>
  );
}
