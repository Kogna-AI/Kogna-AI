"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/app/ui/card";
import { Button } from "@/app/ui/button";
import { Input } from "@/app/ui/input";
import { Label } from "@/app/ui/label";
import { Alert, AlertDescription } from "@/app/ui/alert";
import { AlertCircle, CheckCircle2 } from "lucide-react";
import api from "@/services/api";

function splitName(fullName: string) {
  const parts = fullName.trim().split(/\s+/);
  const firstName = parts[0];
  const secondName = parts.slice(1).join(" ") || "";
  return { firstName, secondName };
}

export default function InviteSignupPage() {
  const params = useParams();
  const router = useRouter();
  const token = params?.token as string;

  const [loading, setLoading] = useState(true);
  const [meta, setMeta] = useState<{
    email: string;
    organization_name: string;
    team_name: string;
  } | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [name, setName] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    const fetchMeta = async () => {
      if (!token) return;
      try {
        const data = await api.getTeamInvitation(token);
        setMeta(data);
        setError(null);
      } catch (e) {
        const message = e instanceof Error ? e.message : "Invalid or expired invitation";
        setError(message);
      } finally {
        setLoading(false);
      }
    };

    fetchMeta();
  }, [token]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!meta) return;

    if (!name.trim()) {
      setError("Please enter your full name");
      return;
    }
    if (password.length < 8) {
      setError("Password must be at least 8 characters long");
      return;
    }
    if (password !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }

    setSubmitting(true);
    setError(null);

    const { firstName, secondName } = splitName(name);

    try {
      await api.acceptTeamInvitation(token, {
        first_name: firstName,
        second_name: secondName,
        password,
      });
      setSuccess(true);
      setTimeout(() => {
        router.push("/login");
      }, 2000);
    } catch (e) {
      const message = e instanceof Error ? e.message : "Failed to accept invitation";
      setError(message);
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-muted-foreground">Loading invitation...</p>
      </div>
    );
  }

  if (error && !meta) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4">
        <Card className="max-w-md w-full">
          <CardContent className="pt-6">
            <div className="flex flex-col items-center gap-4">
              <AlertCircle className="w-8 h-8 text-red-600" />
              <p className="text-red-600 text-center">{error}</p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (success && meta) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4">
        <Card className="max-w-md w-full">
          <CardContent className="pt-6">
            <div className="flex flex-col items-center gap-4">
              <CheckCircle2 className="w-10 h-10 text-green-600" />
              <div className="space-y-2 text-center">
                <h2 className="text-xl font-semibold">Account created</h2>
                <p className="text-sm text-muted-foreground">
                  Your account has been created and you have joined {meta.team_name} at
                  {" "}
                  {meta.organization_name}. Redirecting to login...
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!meta) return null;

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-gradient-to-br from-slate-50 to-slate-100">
      <Card className="max-w-md w-full shadow-xl border-0">
        <CardHeader>
          <CardTitle>Join {meta.team_name}</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-1 text-sm text-muted-foreground">
              <p>
                You are joining <span className="font-medium">{meta.team_name}</span> at
                {" "}
                <span className="font-medium">{meta.organization_name}</span>.
              </p>
              <p>
                Invitation email: <span className="font-mono">{meta.email}</span>
              </p>
            </div>

            <div className="space-y-2 pt-2">
              <Label htmlFor="name">Full name</Label>
              <Input
                id="name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Enter your full name"
              />
            </div>

            <div className="space-y-2">
              <Label>Password</Label>
              <Input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Create a password"
              />
            </div>

            <div className="space-y-2">
              <Label>Confirm password</Label>
              <Input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Re-enter your password"
              />
            </div>

            {error && (
              <Alert variant="destructive">
                <AlertCircle className="w-4 h-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            <Button type="submit" className="w-full" disabled={submitting}>
              {submitting ? "Creating account..." : "Create account"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}