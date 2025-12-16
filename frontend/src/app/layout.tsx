import "./globals.css";
import { QueryProvider } from "./providers/QueryProvider";

export const metadata = {
  title: "My App",
  description: "Layout with sans-serif variable",
};

const rootStyle: React.CSSProperties & { [key: string]: string } = {
  "--font-sans": "ui-sans-serif, system-ui, sans-serif",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" style={rootStyle}>
      <body style={{ fontFamily: "var(--font-sans)" }}>
        <QueryProvider>{children}</QueryProvider>
      </body>
    </html>
  );
}

