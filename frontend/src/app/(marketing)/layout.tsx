// frontend/src/app/(marketing)/layout.tsx
import { LandingNavbar } from "../components/LandingNavbar"; 

export default function MarketingLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex flex-col min-h-screen">
      <LandingNavbar />
      <main className="flex-1">
        {children}
      </main>
    </div>
  );
}