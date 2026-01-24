"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Check, ArrowLeft } from "lucide-react";
import { Button } from "../ui/button";
import { Card } from "../ui/card";
import { useUser } from "../components/auth/UserContext";

interface Plan {
  name: string;
  price: number | null;
  price_display?: string;
  interval: string;
  trial_days?: number;
  features: string[];
}

interface PricingPlans {
  starter: Plan;
  professional: Plan;
  enterprise: Plan;
}

export default function PricingPage() {
  const router = useRouter();
  const { isAuthenticated } = useUser();
  const [plans, setPlans] = useState<PricingPlans | null>(null);
  const [loading, setLoading] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchPlans();
  }, []);

  const fetchPlans = async () => {
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/payments/plans`
      );
      const data = await response.json();
      setPlans(data.plans);
    } catch (err) {
      console.error("Failed to fetch plans:", err);
      setError("Failed to load pricing plans");
    }
  };

  const handleSubscribe = async (planId: string, plan: Plan) => {
    // Check if plan is available
    if (plan.price === null) {
      setError("This plan is not yet available. Please contact sales for more information.");
      return;
    }

    // Check if user is authenticated
    if (!isAuthenticated) {
      // Store the intended plan in sessionStorage to redirect back after login
      sessionStorage.setItem("intended_plan", planId);
      router.push("/login?redirect=pricing");
      return;
    }

    setLoading(planId);
    setError(null);

    try {
      // Import the getAccessToken function to get the current token
      const { getAccessToken } = await import("@/services/api");
      const token = getAccessToken();

      if (!token) {
        router.push("/login?redirect=pricing");
        return;
      }

      // Create checkout session
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/payments/create-checkout-session`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ 
            plan_id: planId
          }),
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to create checkout session");
      }

      const data = await response.json();

      // Redirect to Stripe Checkout
      window.location.href = data.checkout_url;
    } catch (err) {
      console.error("Error:", err);
      setError(err instanceof Error ? err.message : "Failed to start checkout. Please try again.");
      setLoading(null);
    }
  };

  if (!plans) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  const planCards = [
    { id: "starter", plan: plans.starter, recommended: false },
    { id: "professional", plan: plans.professional, recommended: true },
    { id: "enterprise", plan: plans.enterprise, recommended: false },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        {/* Back Button */}
        <div className="mb-8">
          <Button
            onClick={() => router.push("/dashboard")}
            variant="ghost"
            className="flex items-center gap-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Dashboard
          </Button>
        </div>

        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-4">
            Choose Your Plan
          </h1>
          <p className="text-xl text-gray-600 dark:text-gray-300">
            Select the perfect plan for your team's success
          </p>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-8 p-4 bg-red-50 border border-red-200 rounded-lg text-red-800 text-center">
            {error}
          </div>
        )}

        {/* Pricing Cards */}
        <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto">
          {planCards.map(({ id, plan, recommended }) => (
            <Card
              key={id}
              className={`relative p-8 ${
                recommended
                  ? "border-2 border-blue-500 shadow-xl scale-105"
                  : "border border-gray-200"
              }`}
            >
              {recommended && (
                <div className="absolute top-0 left-1/2 transform -translate-x-1/2 -translate-y-1/2">
                  <span className="bg-blue-500 text-white px-4 py-1 rounded-full text-sm font-semibold">
                    Recommended
                  </span>
                </div>
              )}

              <div className="text-center mb-8">
                <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                  {plan.name}
                </h3>
                
                {/* Free Trial Badge */}
                {plan.trial_days && (
                  <div className="mb-3">
                    <span className="inline-block bg-gradient-to-r from-green-500 to-emerald-500 text-white px-4 py-1 rounded-full text-sm font-semibold shadow-lg">
                      🎉 {plan.trial_days} Days Free Trial
                    </span>
                  </div>
                )}
                
                <div className="mt-4">
                  {plan.price !== null ? (
                    <>
                      {plan.trial_days && (
                        <div className="text-sm text-green-600 dark:text-green-400 font-semibold mb-2">
                          Then
                        </div>
                      )}
                      <span className="text-5xl font-bold text-gray-900 dark:text-white">
                        ${plan.price}
                      </span>
                      <span className="text-gray-600 dark:text-gray-400 ml-2">
                        /{plan.interval}
                      </span>
                    </>
                  ) : (
                    <div className="text-4xl font-bold text-gray-500 dark:text-gray-400">
                      Coming Soon
                    </div>
                  )}
                </div>
              </div>

              <ul className="space-y-4 mb-8">
                {plan.features.map((feature, index) => (
                  <li key={index} className="flex items-start">
                    <Check className="h-5 w-5 text-green-500 mr-3 flex-shrink-0 mt-0.5" />
                    <span className="text-gray-700 dark:text-gray-300">
                      {feature}
                    </span>
                  </li>
                ))}
              </ul>

              <Button
                onClick={() => handleSubscribe(id, plan)}
                disabled={loading === id || plan.price === null}
                className={`w-full ${
                  plan.price === null
                    ? "bg-gray-400 cursor-not-allowed"
                    : recommended
                    ? "bg-blue-500 hover:bg-blue-600"
                    : "bg-gray-800 hover:bg-gray-900"
                } text-white py-3 rounded-lg font-semibold transition-colors`}
              >
                {loading === id 
                  ? "Processing..." 
                  : plan.price === null 
                  ? "Contact Sales" 
                  : plan.trial_days
                  ? `Start Free Trial`
                  : "Get Started"}
              </Button>
              
              {plan.trial_days && plan.price !== null && (
                <p className="text-xs text-center text-gray-500 dark:text-gray-400 mt-3">
                  No credit card required for trial
                </p>
              )}
            </Card>
          ))}
        </div>

        {/* FAQ or Additional Info */}
        <div className="mt-16 text-center">
          <p className="text-gray-600 dark:text-gray-400">
            Start with a free trial. Cancel anytime during the trial period.
          </p>
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            Have a promotion code? You can enter it at checkout.
          </p>
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            Need help choosing? <a href="#" className="text-blue-500 hover:underline">Contact our sales team</a>
          </p>
        </div>
      </div>
    </div>
  );
}
