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
import { Eye, EyeOff, AlertCircle, UserPlus } from "lucide-react";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { supabase } from "../../../lib/supabaseClient";
import { useUser } from './UserContext';

const BASE_URL = process.env.NEXT_PUBLIC_BASE_URL;

interface LoginScreenProps {
  onCreateAccount?: () => void;
}

const demoAccounts = [
  {
    name: "Sarah Chen",
    email: "sarah@example.com",
    role: "founder" as const,
  },
  {
    name: "Michael Park",
    email: "michael@example.com",
    role: "executive" as const,
  },
  {
    name: "Emma Wilson",
    email: "emma@example.com",
    role: "manager" as const,
  },
];

export function LoginScreen({ onCreateAccount }: LoginScreenProps) {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");


  // --- Handle login submission ---
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError("");

    try {
      // Attempt to sign in with Supabase Auth
      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password,
      });

      if (error || !data.session) {
        setError("Invalid email or password");
        return;
      }

      // Store the Supabase access token locally
      const {
        data: { session },
      } = await supabase.auth.getSession();
      const token = session?.access_token;
      localStorage.setItem("token", data.session?.access_token);
      // Optional: call FastAPI backend to verify the token
      const response = await fetch(`${BASE_URL}/api/auth/me`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      console.log(await response.json());

      // Redirect user to dashboard after successful login
      // router.push("/mainDashboard");
    } catch (err) {
      console.error(err);
      setError("An unexpected error occurred");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center p-4">
      <div className="w-full max-w-md space-y-6">
        {/* Logo section */}
        <div className="text-center">
          <div className="w-16 h-16 mx-auto mb-4 rounded-xl bg-white shadow-lg flex items-center justify-center">
            <Image
              src="/logoImage.svg"
              alt="KognaDash Logo"
              width={40}
              height={40}
              className="object-contain"
            />
          </div>
          <h1 className="text-2xl font-bold text-gray-900">
            Welcome to KognaDash
          </h1>
          <p className="text-gray-600 mt-1">
            Strategic Team Management Intelligence
          </p>
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

              {/* Submit button */}
              <Button type="submit" className="w-full" disabled={isLoading}>
                {isLoading ? "Signing in..." : "Sign In"}
              </Button>
            </form>
          </CardContent>
        </Card>

        {/* Demo accounts section */}
        <Card className="border-blue-200 bg-blue-50/50">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-blue-900">
              Demo Accounts
            </CardTitle>
            <CardDescription className="text-blue-700">
              Use these accounts to explore KognaDash
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            {demoAccounts.map((account, index) => (
              <div
                key={index}
                className="flex items-center justify-between p-3 bg-white rounded-lg border cursor-pointer hover:border-blue-300 transition-colors"
                onClick={() => {
                  setEmail(account.email);
                  setPassword("demo123");
                }}
              >
                <div>
                  <div className="font-medium text-sm">{account.name}</div>
                  <div className="text-xs text-gray-600">{account.email}</div>
                </div>
                <Badge
                  variant={account.role === "founder" ? "default" : "secondary"}
                >
                  {account.role}
                </Badge>
              </div>
            ))}
            <p className="text-xs text-blue-600 mt-2">
              Password for all demo accounts:{" "}
              <code className="bg-blue-100 px-1 rounded">demo123</code>
            </p>
          </CardContent>
        </Card>
         {onCreateAccount && (
          <Button
            type="button"
            variant="outline"
            className="w-full mt-4"
            onClick={onCreateAccount}
          >
            <UserPlus className="h-4 w-4 mr-2" />
            Create Account
          </Button>
        )}    
      </div>
    </div>
  );
}
