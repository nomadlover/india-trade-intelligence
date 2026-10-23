import type { Metadata, Viewport } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "LEVEL UP | Gamify Your Life & Daily Habits",
  description: "Turn your daily habits into an epic RPG quest. Slay procrastination bosses, earn XP, level up, and unlock real-life rewards on your smartphone.",
  appleWebApp: {
    capable: true,
    statusBarStyle: "black-translucent",
    title: "LEVEL UP",
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
  themeColor: "#0A0D14",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased dark`}
    >
      <body className="min-h-full bg-[#0A0D14] text-slate-100 flex flex-col font-sans select-none overflow-x-hidden">
        {children}
      </body>
    </html>
  );
}
