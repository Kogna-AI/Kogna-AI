import "./globals.css";
import { UserProvider } from "./components/auth/UserContext";

export const metadata = {
  title: "KognaAI",
  description: "Layout with sans-serif variable",
};

const rootStyle: React.CSSProperties & { [key: string]: string } = {
  "--font-sans": "ui-sans-serif, system-ui, sans-serif",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" style={rootStyle}>
      <body style={{ fontFamily: "var(--font-sans)" }}>
        <UserProvider>
        {children}
        </UserProvider>
        </body>
    </html>
  );
}

