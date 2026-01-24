"use client";

import { useState, useEffect } from "react";
import { Button } from "../ui/button";
import { Card } from "../ui/card";
import { CreditCard, Calendar, AlertCircle } from "lucide-react";

interface Subscription {
  has_subscription: boolean;
  plan: string | null;
  status: string | null;
  current_period_end: number | null;
  cancel_at_period_end: boolean;
}

export default function SubscriptionManager() {
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchSubscription();
  }, []);

  const fetchSubscription = async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/payments/subscription`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );
      const data = await response.json();
      setSubscription(data);
    } catch (err) {
      console.error("Failed to fetch subscription:", err);
      setError("Failed to load subscription details");
    } finally {
      setLoading(false);
    }
  };

  const handleManageSubscription = async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/payments/create-portal-session`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );
      const data = await response.json();
      window.location.href = data.url;
    } catch (err) {
      console.error("Failed to create portal session:", err);
      setError("Failed to open subscription management portal");
    }
  };

  if (loading) {
    return (
      <Card className="p-6">
        <div className="flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="p-6">
        <div className="flex items-center text-red-600 dark:text-red-400">
          <AlertCircle className="h-5 w-5 mr-2" />
          <span>{error}</span>
        </div>
      </Card>
    );
  }

  if (!subscription?.has_subscription) {
    return (
      <Card className="p-6">
        <div className="text-center">
          <CreditCard className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
            No Active Subscription
          </h3>
          <p className="text-gray-600 dark:text-gray-400 mb-4">
            Subscribe to unlock all features and grow your team.
          </p>
          <Button
            onClick={() => (window.location.href = "/pricing")}
            className="bg-blue-500 hover:bg-blue-600 text-white"
          >
            View Plans
          </Button>
        </div>
      </Card>
    );
  }

  const formatDate = (timestamp: number) => {
    return new Date(timestamp * 1000).toLocaleDateString("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  };

  return (
    <Card className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-xl font-semibold text-gray-900 dark:text-white">
          Subscription Details
        </h3>
        <span
          className={`px-3 py-1 rounded-full text-sm font-semibold ${
            subscription.status === "active"
              ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
              : "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200"
          }`}
        >
          {subscription.status}
        </span>
      </div>

      <div className="space-y-4 mb-6">
        <div className="flex items-center">
          <CreditCard className="h-5 w-5 text-gray-400 mr-3" />
          <div>
            <p className="text-sm text-gray-600 dark:text-gray-400">Plan</p>
            <p className="font-semibold text-gray-900 dark:text-white capitalize">
              {subscription.plan?.replace("_", " ")}
            </p>
          </div>
        </div>

        {subscription.current_period_end && (
          <div className="flex items-center">
            <Calendar className="h-5 w-5 text-gray-400 mr-3" />
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                {subscription.cancel_at_period_end
                  ? "Expires on"
                  : "Renews on"}
              </p>
              <p className="font-semibold text-gray-900 dark:text-white">
                {formatDate(subscription.current_period_end)}
              </p>
            </div>
          </div>
        )}

        {subscription.cancel_at_period_end && (
          <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
            <div className="flex items-start">
              <AlertCircle className="h-5 w-5 text-yellow-600 dark:text-yellow-400 mr-2 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-yellow-800 dark:text-yellow-200">
                Your subscription will be cancelled at the end of the current
                billing period.
              </p>
            </div>
          </div>
        )}
      </div>

      <Button
        onClick={handleManageSubscription}
        className="w-full bg-gray-800 hover:bg-gray-900 dark:bg-gray-700 dark:hover:bg-gray-600 text-white"
      >
        Manage Subscription
      </Button>

      <p className="text-xs text-gray-500 dark:text-gray-400 text-center mt-4">
        You can update your payment method, change plans, or cancel anytime
      </p>
    </Card>
  );
}
