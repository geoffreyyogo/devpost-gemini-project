/**
 * Theme Switcher Component
 * Toggle between light and dark modes
 */

'use client'

import { useEffect, useState } from 'react'
import { Moon, Sun } from 'lucide-react'
import { Button } from '@/components/ui/button'

export function ThemeSwitcher() {
  const [theme, setTheme] = useState<'light' | 'dark'>('light')
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
    // Check system preference or localStorage
    const savedTheme = localStorage.getItem('theme') as 'light' | 'dark' | null
    const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
    const initialTheme = savedTheme || systemTheme
    
    setTheme(initialTheme)
    if (initialTheme === 'dark') {
      document.documentElement.classList.add('dark')
    }
  }, [])

  const toggleTheme = () => {
    const newTheme = theme === 'light' ? 'dark' : 'light'
    setTheme(newTheme)
    localStorage.setItem('theme', newTheme)
    
    if (newTheme === 'dark') {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }

  // Prevent hydration mismatch
  if (!mounted) {
    return (
      <Button
        variant="ghost"
        size="icon"
        className="w-9 h-9 rounded-full"
        disabled
      >
        <Sun className="h-4 w-4" />
      </Button>
    )
  }

  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={toggleTheme}
      className="w-9 h-9 rounded-full hover:bg-green-100 dark:hover:bg-green-900/30 transition-colors"
      aria-label={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
    >
      {theme === 'light' ? (
        <Moon className="h-4 w-4 text-gray-700 dark:text-gray-300 transition-transform hover:rotate-12" />
      ) : (
        <Sun className="h-4 w-4 text-gray-700 dark:text-gray-300 transition-transform hover:rotate-90" />
      )}
    </Button>
  )
}

