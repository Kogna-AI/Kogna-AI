"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "../../ui/card";
import { Button } from "../../ui/button";
import { Input } from "../../ui/input";
import { Label } from "../../ui/label";
import { Alert, AlertDescription } from "../../ui/alert";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../../ui/select";
import {
  AlertCircle,
  CheckCircle2,
  ArrowLeft,
} from "lucide-react";
import Image from "next/image";

// Pull URL from .env.local
const GOOGLE_SHEET_WEBHOOK_URL = process.env.NEXT_PUBLIC_GOOGLE_SHEET_WEBHOOK_URL;

interface CreateAccountScreenProps {
  onBackToLogin: () => void;
  initialRole?: string;
  lockRole?: boolean;
}

export default function JoinWaitlistPage({
  onBackToLogin,
  initialRole = "",
  lockRole = false,
}: CreateAccountScreenProps) {
  const router = useRouter();

  const [formData, setFormData] = useState({
    name: "",
    email: "",
    organization: "",
    companySize: "",
    role: initialRole,
    phoneNumber: "",
  });

  const [isLoading, setIsLoading] = useState(false);
  const [loadingDots, setLoadingDots] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);

  // Animation Effect
  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (isLoading) {
      setLoadingDots("."); 
      interval = setInterval(() => {
        setLoadingDots((prev) => (prev.length >= 3 ? "." : prev + "."));
      }, 500); 
    } else {
      setLoadingDots("");
    }
    return () => clearInterval(interval); 
  }, [isLoading]);

  // Phone Number Formatting Helper
  const formatPhoneNumber = (value: string) => {
    const phoneNumber = value.replace(/[^\d]/g, "");
    const phoneNumberLength = phoneNumber.length;

    if (phoneNumberLength < 4) return phoneNumber;
    if (phoneNumberLength < 7) {
      return `(${phoneNumber.slice(0, 3)}) ${phoneNumber.slice(3)}`;
    }
    return `(${phoneNumber.slice(0, 3)}) ${phoneNumber.slice(3, 6)}-${phoneNumber.slice(6, 10)}`;
  };

  const handleChange = (field: string, value: string) => {
    let finalValue = value;
    if (field === "phoneNumber") {
      finalValue = formatPhoneNumber(value);
    }
    setFormData((prev) => ({ ...prev, [field]: finalValue }));
    setError("");
  };

  const validateForm = () => {
    if (!formData.name.trim()) {
      setError("Please enter your full name");
      return false;
    }
    if (!formData.email.trim() || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      setError("Please enter a valid email address");
      return false;
    }
    if (!formData.organization.trim()) {
      setError("Please enter your organization name");
      return false;
    }
    if (!formData.companySize) {
      setError("Please select your company size");
      return false;
    }
    if (!formData.role.trim()) {
      setError("Please enter your role");
      return false;
    }
    const rawPhone = formData.phoneNumber.replace(/[^\d]/g, "");
    if (rawPhone.length < 10) {
      setError("Please enter a valid 10-digit phone number");
      return false;
    }
    return true;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateForm()) return;
    
    if (!GOOGLE_SHEET_WEBHOOK_URL) {
      setError("Configuration Error: Webhook URL not found.");
      return;
    }

    setIsLoading(true);
    setError("");

    try {
      await fetch(GOOGLE_SHEET_WEBHOOK_URL, {
        method: "POST",
        mode: "no-cors", 
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(formData),
      });

      setSuccess(true);
      setTimeout(() => {
        router.push('/'); 
      }, 2000);

    } catch (err) {
      console.error(err);
      setError("Failed to submit information. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  if (success) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center p-4">
        <Card className="w-full max-w-md shadow-xl border-0">
          <CardContent className="pt-6">
            <div className="text-center space-y-4">
              <div className="w-16 h-16 mx-auto rounded-full bg-green-100 flex items-center justify-center">
                <CheckCircle2 className="w-8 h-8 text-green-600" />
              </div>
              <div>
                <h2 className="text-2xl font-bold text-gray-900">Success!</h2>
                <p className="text-gray-600 mt-2">You've joined the list. We'll be in touch soon.</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center p-4">
      <div className="w-full max-w-md space-y-6">
        <div className="text-center">
          <div className="w-16 h-16 mx-auto mb-4 rounded-xl bg-white shadow-lg flex items-center justify-center">
            <Image src="/localImage.png" alt="KognaDash Logo" width={40} height={40} className="object-contain" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900">Join Kogna</h1>
          <p className="text-gray-600 mt-1">Strategic Intelligence</p>
        </div>

        <Card className="shadow-xl border-0">
          <CardHeader className="space-y-1">
            <CardTitle className="text-xl">Join the Waitlist</CardTitle>
            <CardDescription>
              Get first access to <strong>beta</strong> and <strong>pre-launch</strong>
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="name">Full Name</Label>
                {/* Reverted to default sizing */}
                <Input 
                  id="name" 
                  placeholder="Enter your full name" 
                  value={formData.name} 
                  onChange={(e) => handleChange("name", e.target.value)} 
                  required 
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                {/* Reverted to default sizing */}
                <Input 
                  id="email" 
                  type="email" 
                  placeholder="Enter your email" 
                  value={formData.email} 
                  onChange={(e) => handleChange("email", e.target.value)} 
                  required 
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="organization">Organization</Label>
                {/* Reverted to default sizing */}
                <Input 
                  id="organization" 
                  placeholder="Your company or organization" 
                  value={formData.organization} 
                  onChange={(e) => handleChange("organization", e.target.value)} 
                  required 
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="companySize">Company Size</Label>
                <Select 
                    value={formData.companySize} 
                    onValueChange={(value) => handleChange("companySize", value)}
                >
                    {/* CHANGED: This now matches the input behavior exactly (16px mobile -> 14px desktop) */}
                    <SelectTrigger id="companySize" className="w-full text-base md:text-sm">
                      <SelectValue placeholder="How many employees?" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="1-10">1-10 employees</SelectItem>
                      <SelectItem value="11-50">11-50 employees</SelectItem>
                      <SelectItem value="51-200">51-200 employees</SelectItem>
                      <SelectItem value="201-500">201-500 employees</SelectItem>
                      <SelectItem value="500+">500+ employees</SelectItem>
                    </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="role">Role</Label>
                {/* Reverted to default sizing */}
                <Input 
                  id="role" 
                  placeholder="e.g. Founder, CTO, Product Manager" 
                  value={formData.role} 
                  onChange={(e) => handleChange("role", e.target.value)} 
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="phoneNumber">Phone Number</Label>
                {/* Reverted to default sizing */}
                <Input 
                  id="phoneNumber" 
                  type="tel"
                  placeholder="(123) 456-7890" 
                  value={formData.phoneNumber} 
                  onChange={(e) => handleChange("phoneNumber", e.target.value)} 
                  required 
                />
              </div>

              {error && (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}

              <Button type="submit" className="w-full" disabled={isLoading}>
                {isLoading ? `Joining Waitlist${loadingDots}` : "Join Waitlist"}
              </Button>

              <div className="text-center pt-2">
                <Button 
                  type="button" 
                  variant="ghost" 
                  size="sm" 
                  onClick={() => router.push('/')}
                  className="text-gray-600"
                >
                  <ArrowLeft className="w-4 h-4 mr-1" />
                  Back to Landing Page
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}