import "./globals.css";
import { ThemeProvider } from "../contexts/ThemeContext";
import { ConversationProvider } from "../contexts/ConversationContext";
import AppLayout from "../components/app-layout/app-layout";
import 'katex/dist/katex.min.css';

/**
 * Metadata configuration for the Next.js application
 * Used for SEO and browser tab information
 */
export const metadata = {
  title: "ChatPLG",
  description: "A Hebrew RTL chatbot application built with React and Next.js",
  robots: "index, follow",
};

/**
 * Root layout component for the entire application
 * Provides theme and conversation context to all child components
 * Sets up the HTML structure with Hebrew language and RTL direction
 */
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
            <AppLayout>
              {children}
            </AppLayout>
          </ConversationProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
