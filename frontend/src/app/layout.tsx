import type { Metadata } from "next"
import { Inter } from "next/font/google"
import "./globals.css"
import { Toaster } from "@/components/ui/toaster"
import { FloraChatWidget } from "@/components/chat/FloraChat"
import { ThemeProvider } from "@/components/providers/theme-provider"

const inter = Inter({ subsets: ["latin"] })

export const metadata: Metadata = {
  title: "Shamba Smart - Smart Crop Monitoring",
  description: "NASA-powered bloom tracking platform for Kenyan farmers. Monitor crop health, receive bloom alerts, and optimize harvest timing.",
  keywords: ["agriculture", "Kenya", "crop monitoring", "bloom detection", "farming", "satellite data", "NDVI"],
  authors: [{ name: "Geoffrey Yogo" }],
  openGraph: {
    type: "website",
    locale: "en_KE",
    url: "https://bloomwatch.co.ke",
    title: "Shamba Smart - Smart Crop Monitoring",
    description: "NASA-powered bloom tracking platform for Kenyan farmers",
    siteName: "Shamba Smart",
  },
  twitter: {
    card: "summary_large_image",
    title: "Shamba Smart - Smart Crop Monitoring",
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
          {children}
          <FloraChatWidget />
          <Toaster />
        </ThemeProvider>
      </body>
    </html>
  )
}

