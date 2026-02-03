"use client";

import { useState } from "react";
import { Badge } from "../../ui/badge";
import { Button } from "../../ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "../../ui/card";
import { Input } from "../../ui/input";
import { Label } from "../../ui/label";
import { Alert, AlertDescription } from "../../ui/alert";
import { Eye, EyeOff, AlertCircle, UserPlus, Loader2 } from "lucide-react"; // ✅ Added Loader2
import Image from "next/image";
import { useRouter } from "next/navigation";
import { useUser } from "./UserContext";
import api from "@/services/api"; // ✅ Added api import

const BASE_URL = process.env.NEXT_PUBLIC_BASE_URL;

interface LoginScreenProps {
  onCreateAccount?: () => void;
}

export function LoginScreen({ onCreateAccount }: LoginScreenProps) {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  
  // ✅ Added email verification states
  const [showResend, setShowResend] = useState(false);
  const [resendLoading, setResendLoading] = useState(false);
  const [resendMessage, setResendMessage] = useState("");

  // Handle signup navigation
  const handleSignupClick = () => {
    if (onCreateAccount) {
      onCreateAccount();
    } else {
      router.push("/signup");
    }
  };

  // --- Handle login submission ---
  const { login } = useUser();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError("");
    setShowResend(false); // ✅ Reset resend button

    try {
      const success = await login(email, password);

      if (!success) {
        setError("Login failed");
        return;
      }

      // IMPORTANT: use replace, not push
      router.replace("/dashboard");
    } catch (err: any) {
      console.error(err);
      const errorMessage = err?.message || "An unexpected error occurred";
      setError(errorMessage);
      
      // ✅ Show resend button if email not verified
      if (errorMessage.includes("verify your email") || errorMessage.includes("not verified")) {
        setShowResend(true);
      }
    } finally {
      setIsLoading(false);
    }
  };

  // ✅ Added resend verification handler
  const handleResendVerification = async () => {
    setResendLoading(true);
    setResendMessage("");

    try {
      const data = await api.resendVerification(email);
      setResendMessage(data.message || "✓ Verification email sent! Check your inbox.");
    } catch (error: any) {
      setResendMessage(error.message || "Failed to resend email");
    } finally {
      setResendLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center p-4">
      <div className="w-full max-w-md space-y-6">
        {/* Logo section */}
        <div className="text-center">
          <div className="w-16 h-16 mx-auto mb-4 rounded-xl bg-white shadow-lg flex items-center justify-center">
            <Image
              src="/localImage.png"
              alt="KognaDash Logo"
              width={40}
              height={40}
              className="object-contain"
            />
          </div>
          <h1 className="text-2xl font-bold text-gray-900">
            Welcome to Kogna
          </h1>
          <p className="text-gray-600 mt-1">Strategic Intelligence</p>
        </div>

        {/* Login form */}
        <Card className="shadow-xl border-0">
          <CardHeader className="space-y-1">
            <CardTitle className="text-xl">Sign in to your account</CardTitle>
            <CardDescription>
              Enter your credentials to access your dashboard
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Email input */}
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="Enter your email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>

              {/* Password input */}
              <div className="space-y-2">
                <Label htmlFor="password">Password</Label>
                <div className="relative">
                  <Input
                    id="password"
                    type={showPassword ? "text" : "password"}
                    placeholder="Enter your password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                  />
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                    onClick={() => setShowPassword(!showPassword)}
                  >
                    {showPassword ? (
                      <EyeOff className="h-4 w-4 text-gray-400" />
                    ) : (
                      <Eye className="h-4 w-4 text-gray-400" />
                    )}
                  </Button>
                </div>
              </div>

              {/* Error alert */}
              {error && (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}

              {/* ✅ Resend verification button */}
              {showResend && (
                <div className="text-center">
                  <Button
                    type="button"
                    variant="ghost"
                    onClick={handleResendVerification}
                    disabled={resendLoading}
                    className="text-sm text-blue-600 hover:text-blue-700"
                  >
                    {resendLoading ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        Sending...
                      </>
                    ) : (
                      "Resend verification email"
                    )}
                  </Button>
                </div>
              )}

              {/* ✅ Resend message */}
              {resendMessage && (
                <Alert className={`${
                  resendMessage.includes("✓")
                    ? "bg-green-50 border-green-200"
                    : "bg-red-50 border-red-200"
                }`}>
                  <AlertDescription className={`text-sm ${
                    resendMessage.includes("✓") ? "text-green-700" : "text-red-700"
                  }`}>
                    {resendMessage}
                  </AlertDescription>
                </Alert>
              )}

              {/* Submit button */}
              <Button type="submit" className="w-full" disabled={isLoading}>
                {isLoading ? "Signing in..." : "Sign In"}
              </Button>
            </form>
          </CardContent>
        </Card>

        {/* Waitlist section */}
        <div className="text-center space-y-3">
          <p className="text-sm text-gray-600">Don't have an account yet?</p>
          <Button
            type="button"
            variant="outline"
            className="w-full h-11 border-gray-300 hover:bg-gray-50"
            onClick={handleSignupClick}
          >
            <UserPlus className="h-4 w-4 mr-2" />
            Join the Waitlist
          </Button>
        </div>
      </div>
    </div>
  );
}
