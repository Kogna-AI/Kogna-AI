import { useState } from "react";
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
  Eye,
  EyeOff,
  AlertCircle,
  CheckCircle2,
  ArrowLeft,
  Check,
} from "lucide-react";
import Image from "next/image";
import { useUser } from "./UserContext";

interface CreateAccountScreenProps {
  onBackToLogin: () => void;
  initialRole?: "founder" | "executive" | "manager" | "member";
  lockRole?: boolean; // when true, hide role selector and keep initialRole fixed
}

function splitName(fullName: string) {
  const parts = fullName.trim().split(/\s+/);

  const firstName = parts[0];
  const secondName = parts.slice(1).join(" ") || "";

  return { firstName, secondName };
}

export default function CreateAccountPage({
  onBackToLogin,
  initialRole = "founder",
  lockRole = false,
}: CreateAccountScreenProps) {
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    password: "",
    confirmPassword: "",
    role: initialRole as "founder" | "executive" | "manager" | "member",
    organization: "",
  });

  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);
  const { signup } = useUser();

  const handleChange = (field: string, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    setError("");
  };

  // Enhanced password strength checker
  const getPasswordStrength = (pwd: string) => {
    if (pwd.length === 0)
      return { strength: 0, label: "", color: "bg-gray-200" };
    if (pwd.length < 8)
      return { strength: 1, label: "Weak", color: "bg-red-500" };

    let strength = 1;
    if (pwd.length >= 12) strength++;
    if (/[a-z]/.test(pwd) && /[A-Z]/.test(pwd)) strength++;
    if (/\d/.test(pwd)) strength++;
    if (/[^a-zA-Z0-9]/.test(pwd)) strength++;

    if (strength <= 2)
      return { strength: 1, label: "Weak", color: "bg-red-500" };
    if (strength === 3)
      return { strength: 2, label: "Medium", color: "bg-yellow-500" };
    return { strength: 3, label: "Strong", color: "bg-green-500" };
  };

  const passwordStrength = getPasswordStrength(formData.password);
  const passwordsMatch =
    formData.password === formData.confirmPassword &&
    formData.confirmPassword.length > 0;

  const validateForm = () => {
    if (!formData.name.trim()) {
      setError("Please enter your full name");
      return false;
    }
    if (
      !formData.email.trim() ||
      !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)
    ) {
      setError("Please enter a valid email address");
      return false;
    }
    if (formData.password.length < 8) {
      setError("Password must be at least 8 characters long");
      return false;
    }
    if (formData.password !== formData.confirmPassword) {
      setError("Passwords do not match");
      return false;
    }
    if (!formData.organization.trim()) {
      setError("Please enter your organization name");
      return false;
    }
    return true;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateForm()) return;
    setIsLoading(true);
    setError("");

    const { firstName, secondName } = splitName(formData.name);
    try {
      const result = await signup({
        first_name: firstName,
        second_name: secondName,
        email: formData.email,
        password: formData.password,
        role: formData.role,
        organization: formData.organization,
      });
      if (result.success) {
        setSuccess(true);
        setTimeout(() => {
          onBackToLogin();
        }, 2000);
      } else {
        setError(result.error || "Failed to create account");
      }
    } catch (err) {
      setError("An unexpected error occurred");
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
                <h2 className="text-2xl font-bold text-gray-900">
                  Account Created!
                </h2>
                <p className="text-gray-600 mt-2">
                  Welcome to KognaDash, {formData.name}. Redirecting you to
                  login...
                </p>
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
          <h1 className="text-2xl font-bold text-gray-900">Join KognaDash</h1>
          <p className="text-gray-600 mt-1">
            Strategic Team Management Intelligence
          </p>
        </div>

        {/* Account creation form */}
        <Card className="shadow-xl border-0">
          <CardHeader className="space-y-1">
            <CardTitle className="text-xl">Create your account</CardTitle>
            <CardDescription>
              Get started with AI-powered team management
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Full Name */}
              <div className="space-y-2">
                <Label htmlFor="name">Full Name</Label>
                <Input
                  id="name"
                  type="text"
                  placeholder="Enter your full name"
                  value={formData.name}
                  onChange={(e) => handleChange("name", e.target.value)}
                  required
                />
              </div>

              {/* Email */}
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="Enter your email"
                  value={formData.email}
                  onChange={(e) => handleChange("email", e.target.value)}
                  required
                />
              </div>

              {/* Organization */}
              <div className="space-y-2">
                <Label htmlFor="organization">Organization</Label>
                <Input
                  id="organization"
                  type="text"
                  placeholder="Your company or organization"
                  value={formData.organization}
                  onChange={(e) => handleChange("organization", e.target.value)}
                  required
                />
              </div>

              {/* Role */}
              {!lockRole && (
                <div className="space-y-2">
                  <Label htmlFor="role">Role</Label>
                  <Select
                    value={formData.role}
                    onValueChange={(value) => handleChange("role", value)}
                  >
                    <SelectTrigger id="role">
                      <SelectValue placeholder="Select your role" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="founder">Founder / CEO</SelectItem>
                      <SelectItem value="executive">Executive / VP</SelectItem>
                      <SelectItem value="manager">Manager / Team Lead</SelectItem>
                      <SelectItem value="member">Team Member</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              )}

              {/* Password */}
              <div className="space-y-2">
                <Label htmlFor="password">Password</Label>
                <div className="relative">
                  <Input
                    id="password"
                    type={showPassword ? "text" : "password"}
                    placeholder="Create a strong password"
                    value={formData.password}
                    onChange={(e) => handleChange("password", e.target.value)}
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
                {/* Enhanced password strength indicator */}
                {formData.password.length > 0 && (
                  <div className="space-y-1">
                    <div className="flex gap-1">
                      <div
                        className={`h-1 flex-1 rounded ${
                          passwordStrength.strength >= 1
                            ? passwordStrength.color
                            : "bg-gray-200"
                        }`}
                      />
                      <div
                        className={`h-1 flex-1 rounded ${
                          passwordStrength.strength >= 2
                            ? passwordStrength.color
                            : "bg-gray-200"
                        }`}
                      />
                      <div
                        className={`h-1 flex-1 rounded ${
                          passwordStrength.strength >= 3
                            ? passwordStrength.color
                            : "bg-gray-200"
                        }`}
                      />
                    </div>
                    <p className="text-xs text-gray-600">
                      Password strength: {passwordStrength.label}
                    </p>
                  </div>
                )}
                <p className="text-xs text-gray-500">
                  Use 8+ characters with uppercase, lowercase, and numbers
                </p>
              </div>

              {/* Confirm Password */}
              <div className="space-y-2">
                <Label htmlFor="confirmPassword">Confirm Password</Label>
                <div className="relative">
                  <Input
                    id="confirmPassword"
                    type={showConfirmPassword ? "text" : "password"}
                    placeholder="Re-enter your password"
                    value={formData.confirmPassword}
                    onChange={(e) =>
                      handleChange("confirmPassword", e.target.value)
                    }
                    required
                  />
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  >
                    {showConfirmPassword ? (
                      <EyeOff className="h-4 w-4 text-gray-400" />
                    ) : (
                      <Eye className="h-4 w-4 text-gray-400" />
                    )}
                  </Button>
                </div>
                {/* Password match indicator */}
                {formData.confirmPassword.length > 0 && (
                  <div className="flex items-center gap-1">
                    {passwordsMatch ? (
                      <>
                        <Check className="h-3 w-3 text-green-600" />
                        <p className="text-xs text-green-600">
                          Passwords match
                        </p>
                      </>
                    ) : (
                      <p className="text-xs text-red-600">
                        Passwords do not match
                      </p>
                    )}
                  </div>
                )}
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
                {isLoading ? "Creating Account..." : "Create Account"}
              </Button>

              {/* Back to login */}
              <div className="text-center pt-2">
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={onBackToLogin}
                  className="text-gray-600"
                >
                  <ArrowLeft className="w-4 h-4 mr-1" />
                  Back to Login
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>

        {/* Terms and privacy */}
        <Card className="border-blue-200 bg-blue-50/50">
          <CardContent className="pt-4">
            <p className="text-xs text-blue-700 text-center">
              By creating an account, you agree to our Terms of Service and
              Privacy Policy. Your data is secured with industry-standard
              encryption.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
