"use client";

import { useRouter } from "next/navigation";
import { XCircle } from "lucide-react";
import { Button } from "../../ui/button";

export default function PaymentCancelPage() {
  const router = useRouter();

  return (
    <div className="min-h-screen bg-gradient-to-br from-red-50 to-orange-50 dark:from-gray-900 dark:to-gray-800 flex items-center justify-center px-4">
      <div className="max-w-md w-full bg-white dark:bg-gray-800 rounded-2xl shadow-xl p-8 text-center">
        <div className="flex justify-center mb-6">
          <XCircle className="h-20 w-20 text-orange-500" />
        </div>

        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-4">
          Payment Cancelled
        </h1>

        <p className="text-gray-600 dark:text-gray-300 mb-8">
          Your payment was cancelled. No charges have been made to your account.
        </p>

        <div className="space-y-3">
          <Button
            onClick={() => router.push("/pricing")}
            className="w-full bg-blue-500 hover:bg-blue-600 text-white py-3 rounded-lg font-semibold"
          >
            Try Again
          </Button>
          
          <Button
            onClick={() => router.push("/dashboard")}
            className="w-full bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-900 dark:text-white py-3 rounded-lg font-semibold"
          >
            Return to Dashboard
          </Button>
        </div>

        <p className="text-sm text-gray-500 dark:text-gray-400 mt-6">
          Need help? <a href="#" className="text-blue-500 hover:underline">Contact support</a>
        </p>
      </div>
    </div>
  );
}
