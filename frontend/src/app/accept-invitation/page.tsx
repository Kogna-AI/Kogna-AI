"use client";

import { useState, useEffect, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/app/ui/card";
import { Button } from "@/app/ui/button";
import { Input } from "@/app/ui/input";
import { Label } from "@/app/ui/label";
import { Alert, AlertDescription } from "@/app/ui/alert";
import {
  Loader2,
  CheckCircle2,
  AlertCircle,
  UserPlus,
  ShieldCheck,
} from "lucide-react";
import Image from "next/image";
import api from "@/services/api";

function AcceptInvitationContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get("token");

  // State for invitation metadata
  const [invitationMeta, setInvitationMeta] = useState<{
    email: string;
    organization_name: string;
    team_name: string;
  } | null>(null);

  // Form state
  const [firstName, setFirstName] = useState("");
  const [secondName, setSecondName] = useState("");
  const [password, setPassword] = useState("");

  const [isLoading, setIsLoading] = useState(false);
  const [isVerifying, setIsVerifying] = useState(true);
  const [error, setError] = useState("");
  const [isSuccess, setIsSuccess] = useState(false);

  // Step 1: Verify token on load
  useEffect(() => {
    const verifyInvitation = async () => {
      if (!token) {
        setError("Missing invitation token.");
        setIsVerifying(false);
        return;
      }

      try {
        const data = await api.getTeamInvitation(token);
        setInvitationMeta(data);
      } catch (err: any) {
        setError(err.message || "Invitation link is invalid or has expired.");
      } finally {
        setIsVerifying(false);
      }
    };

    verifyInvitation();
  }, [token]);

  // Step 2: Handle submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) return;

    setIsLoading(true);
    setError("");

    try {
      await api.acceptTeamInvitation(token, {
        first_name: firstName,
        second_name: secondName,
        password: password,
      });

      setIsSuccess(true);

      // Redirect to login after 3 seconds
      setTimeout(() => {
        router.push("/login");
      }, 3000);
    } catch (err: any) {
      setError(err.message || "Failed to accept invitation. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  if (isVerifying) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center space-y-4">
          <Loader2 className="w-10 h-10 animate-spin text-purple-600 mx-auto" />
          <p className="text-gray-500 font-medium">
            Validating your invitation...
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center p-4">
      <div className="w-full max-w-md space-y-6">
        {/* Logo */}
        <div className="text-center">
          <div className="w-16 h-16 mx-auto mb-4 rounded-xl bg-white shadow-lg flex items-center justify-center">
            <Image src="/localImage.png" alt="Logo" width={40} height={40} />
          </div>
          <h1 className="text-2xl font-bold text-gray-900">Join the Team</h1>
        </div>

        <Card className="shadow-xl border-0">
          <CardHeader>
            <CardTitle className="text-xl flex items-center gap-2">
              <ShieldCheck className="text-green-600 w-5 h-5" />
              Invitation Accepted
            </CardTitle>
            {invitationMeta && (
              <CardDescription>
                You have been invited to join{" "}
                <strong>{invitationMeta.team_name}</strong> at{" "}
                <strong>{invitationMeta.organization_name}</strong>.
              </CardDescription>
            )}
          </CardHeader>

          <CardContent>
            {isSuccess ? (
              <div className="py-6 text-center space-y-4">
                <div className="w-12 h-12 bg-green-100 text-green-600 rounded-full flex items-center justify-center mx-auto">
                  <CheckCircle2 className="w-8 h-8" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900">
                  Welcome aboard!
                </h3>
                <p className="text-gray-500">
                  Your account has been created. Redirecting to login...
                </p>
              </div>
            ) : error ? (
              <div className="space-y-4">
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
                <Button
                  className="w-full"
                  onClick={() => router.push("/login")}
                >
                  Return to Login
                </Button>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="firstName">First Name</Label>
                    <Input
                      id="firstName"
                      placeholder="John"
                      value={firstName}
                      onChange={(e) => setFirstName(e.target.value)}
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="secondName">Last Name</Label>
                    <Input
                      id="secondName"
                      placeholder="Doe"
                      value={secondName}
                      onChange={(e) => setSecondName(e.target.value)}
                      required
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="email">Email Address</Label>
                  <Input
                    id="email"
                    type="email"
                    value={invitationMeta?.email || ""}
                    disabled
                    className="bg-gray-50 cursor-not-allowed"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="password">Set Password</Label>
                  <Input
                    id="password"
                    type="password"
                    placeholder="Min. 8 characters"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                  />
                </div>

                <Button
                  type="submit"
                  className="w-full bg-purple-600 hover:bg-purple-700 text-white mt-4"
                  disabled={isLoading}
                >
                  {isLoading ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />{" "}
                      Joining...
                    </>
                  ) : (
                    "Complete Registration"
                  )}
                </Button>
              </form>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

// Main page component with Suspense for SearchParams
export default function AcceptInvitationPage() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <AcceptInvitationContent />
    </Suspense>
  );
}
