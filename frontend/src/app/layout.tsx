import type { Metadata } from "next"
import { Inter } from "next/font/google"
import "./globals.css"
import "@/lib/i18n"
import { Toaster } from "@/components/ui/toaster"
import { FloraChatWidget } from "@/components/chat/FloraChat"
import { ThemeProvider } from "@/components/providers/theme-provider"
import { QueryProvider } from "@/components/providers/query-provider"

const inter = Inter({ subsets: ["latin"] })

export const metadata: Metadata = {
  title: "Smart Shamba - Smart Crop Monitoring",
  description: "NASA-powered bloom tracking platform for Kenyan farmers. Monitor crop health, receive bloom alerts, and optimize harvest timing.",
  keywords: ["agriculture", "Kenya", "crop monitoring", "bloom detection", "farming", "satellite data", "NDVI"],
  authors: [{ name: "Geoffrey Yogo" }],
  openGraph: {
    type: "website",
    locale: "en_KE",
    url: "https://bloomwatch.co.ke",
    title: "Smart Shamba - Smart Crop Monitoring",
    description: "NASA-powered bloom tracking platform for Kenyan farmers",
    siteName: "Smart Shamba",
  },
  twitter: {
    card: "summary_large_image",
    title: "Smart Shamba - Smart Crop Monitoring",
    description: "NASA-powered bloom tracking platform for Kenyan farmers",
  },
  robots: {
    index: true,
    follow: true,
  },
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <ThemeProvider
          attribute="class"
          defaultTheme="light"
          enableSystem
          disableTransitionOnChange
        >
          <QueryProvider>
            {children}
            <FloraChatWidget />
          </QueryProvider>
          <Toaster />
        </ThemeProvider>
      </body>
    </html>
  )
}

