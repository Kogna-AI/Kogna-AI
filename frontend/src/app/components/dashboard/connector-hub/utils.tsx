import { CheckCircle, Clock, Star } from "lucide-react";

export const getStatusIcon = (status: string) => {
  switch (status) {
    case "connected":
      return <CheckCircle className="w-4 h-4 text-green-500" />;
    case "premium":
      return <Star className="w-4 h-4 text-amber-500" />;
    default:
      return <Clock className="w-4 h-4 text-gray-400" />;
  }
};

export const getStatusText = (status: string) => {
  switch (status) {
    case "connected":
      return "Connected";
    case "premium":
      return "Premium";
    default:
      return "Available";
  }
};
