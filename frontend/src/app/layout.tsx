import { AppProviders } from "./providers/AppProvider";
import "./globals.css";

export const metadata = {
  title: "Kogna",
  description: "Layout with sans-serif variable",
};

const rootStyle: React.CSSProperties & { [key: string]: string } = {
  "--font-sans": "ui-sans-serif, system-ui, sans-serif",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body style={{ fontFamily: "var(--font-sans)" }}>
        <AppProviders>{children}</AppProviders>
      </body>
    </html>
  );
}
