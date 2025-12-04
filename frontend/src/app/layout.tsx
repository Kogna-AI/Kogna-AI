import "./globals.css";

export const metadata = {
  title: "My App",
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
    <html lang="en" style={rootStyle}>
      <body style={{ fontFamily: "var(--font-sans)" }}>{children}</body>
    </html>
  );
}
