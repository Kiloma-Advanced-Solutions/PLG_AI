import "./globals.css";
import { ThemeProvider } from "../contexts/ThemeContext";
import { ConversationProvider } from "../contexts/ConversationContext";

export const metadata = {
  title: "ChatPLG",
  description: "A Hebrew RTL chatbot application built with React and Next.js",
  robots: "index, follow",
};

export const viewport = {
  width: "device-width",
  initialScale: 1,
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
          <ConversationProvider>
            {children}
          </ConversationProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
