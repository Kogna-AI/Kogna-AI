"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/app/ui/card";
import { Button } from "@/app/ui/button";
import { Input } from "@/app/ui/input";
import { Label } from "@/app/ui/label";
import { ArrowRight, ArrowLeft, Users, UserPlus } from "lucide-react";

export default function SignupLandingPage() {
  const router = useRouter();
  const [inviteValue, setInviteValue] = useState("");
  const [error, setError] = useState<string | null>(null);

  const handleFounder = () => {
    router.push("/signup/founder");
  };

  const handleInviteContinue = () => {
    setError(null);
    const raw = inviteValue.trim();
    if (!raw) {
      setError("Please paste your invite link or code");
      return;
    }

    let token = raw;
    try {
      // If it's a full URL, extract last path segment
      const url = new URL(raw);
      const parts = url.pathname.split("/").filter(Boolean);
      token = parts[parts.length - 1] || "";
    } catch {
      // Not a URL – allow things like just the token or trailing slash
      const parts = raw.split("/").filter(Boolean);
      token = parts[parts.length - 1] || "";
    }

    if (!token) {
      setError("Could not detect a valid invite code");
      return;
    }

    router.push(`/signup/invite/${token}`);
  };

  return (
    <>
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center p-4">
        <Card className="w-full max-w-4xl shadow-xl border-0">
          <CardHeader className="space-y-2 text-center">
            <CardTitle className="text-2xl">
              Create your Kogna account
            </CardTitle>
            <CardDescription>
              Choose how you want to get started: create a new organization or
              join with an invite.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="grid gap-4 md:grid-cols-2">
              <Button
                type="button"
                variant="default"
                className="h-auto p-4 flex flex-col items-start gap-2 text-left"
                onClick={handleFounder}
              >
                <div className="flex items-center gap-2">
                  <Users className="w-5 h-5" />
                  <span className="font-medium">
                    I&apos;m starting an organization
                  </span>
                </div>
                <span className="text-xs text-muted-foreground">
                  Create a new workspace, organization, and initial team.
                </span>
              </Button>

              <div className="space-y-2 border rounded-lg p-4">
                <div className="flex items-center gap-2 mb-1">
                  <UserPlus className="w-4 h-4" />
                  <span className="font-medium text-sm">
                    I have an invite link or code
                  </span>
                </div>
                <p className="text-xs text-muted-foreground mb-2">
                  Paste the invite link you received by email, or just the
                  invite code.
                </p>
                <Label htmlFor="invite">Invite link or code</Label>
                <Input
                  id="invite"
                  value={inviteValue}
                  onChange={(e) => setInviteValue(e.target.value)}
                  placeholder="https://kogna.io/signup/invite/abcd-1234 ..."
                />
                {error && <p className="text-xs text-red-600 mt-1">{error}</p>}
                <div className="flex justify-end mt-2">
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={handleInviteContinue}
                  >
                    Continue
                    <ArrowRight className="w-4 h-4 ml-1" />
                  </Button>
                </div>
              </div>
            </div>
            <div className="flex justify-center">
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={() => router.push("/login")}
                className="text-gray-600"
              >
                <ArrowLeft className="w-4 h-4 mr-1" />
                Back to Login
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </>
  );
}
