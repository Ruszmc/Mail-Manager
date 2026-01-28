import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "MailPilot",
  description: "AI-assisted email client",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="de">
      <body>{children}</body>
    </html>
  );
}
