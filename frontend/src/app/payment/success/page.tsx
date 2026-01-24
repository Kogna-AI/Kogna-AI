"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { CheckCircle } from "lucide-react";
import { Button } from "../../ui/button";

export default function PaymentSuccessPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [sessionDetails, setSessionDetails] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const sessionId = searchParams.get("session_id");
    if (sessionId) {
      fetchSessionDetails(sessionId);
    } else {
      setLoading(false);
    }
  }, [searchParams]);

  const fetchSessionDetails = async (sessionId: string) => {
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/payments/session/${sessionId}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );
      const data = await response.json();
      setSessionDetails(data);
    } catch (err) {
      console.error("Failed to fetch session details:", err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-50 dark:from-gray-900 dark:to-gray-800 flex items-center justify-center px-4">
      <div className="max-w-md w-full bg-white dark:bg-gray-800 rounded-2xl shadow-xl p-8 text-center">
        <div className="flex justify-center mb-6">
          <CheckCircle className="h-20 w-20 text-green-500" />
        </div>

        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-4">
          Payment Successful!
        </h1>

        <p className="text-gray-600 dark:text-gray-300 mb-6">
          Thank you for subscribing to Kogna AI. Your payment has been processed
          successfully.
        </p>

        {sessionDetails && (
          <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 mb-6 text-left">
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-gray-600 dark:text-gray-400">Status:</span>
                <span className="font-semibold text-green-600 dark:text-green-400">
                  {sessionDetails.status}
                </span>
              </div>
              {sessionDetails.customer_email && (
                <div className="flex justify-between">
                  <span className="text-gray-600 dark:text-gray-400">Email:</span>
                  <span className="font-semibold text-gray-900 dark:text-white">
                    {sessionDetails.customer_email}
                  </span>
                </div>
              )}
              {sessionDetails.amount_total && (
                <div className="flex justify-between">
                  <span className="text-gray-600 dark:text-gray-400">Amount:</span>
                  <span className="font-semibold text-gray-900 dark:text-white">
                    ${(sessionDetails.amount_total / 100).toFixed(2)}
                  </span>
                </div>
              )}
            </div>
          </div>
        )}

        <div className="space-y-3">
          <Button
            onClick={() => router.push("/dashboard")}
            className="w-full bg-blue-500 hover:bg-blue-600 text-white py-3 rounded-lg font-semibold"
          >
            Go to Dashboard
          </Button>
          
          <Button
            onClick={() => router.push("/settings")}
            className="w-full bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-900 dark:text-white py-3 rounded-lg font-semibold"
          >
            Manage Subscription
          </Button>
        </div>

        <p className="text-sm text-gray-500 dark:text-gray-400 mt-6">
          You will receive a confirmation email shortly.
        </p>
      </div>
    </div>
  );
}
