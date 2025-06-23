import type { Metadata } from "next";
import "./globals.css";
import { ThemeProvider } from "../contexts/ThemeContext";

export const metadata: Metadata = {
  title: "ChatPLG",
  description: "A Hebrew RTL chatbot application built with React and Next.js",
  viewport: "width=device-width, initial-scale=1",
  robots: "index, follow",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="he" dir="rtl">
      <body>
        <ThemeProvider>
          {children}
        </ThemeProvider>
      </body>
    </html>
  );
}
