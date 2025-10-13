/**
 * Language Selector Component
 * Switch between English and Swahili
 */

'use client'

import { useState, useRef, useEffect } from 'react'
import { Globe, Check, ChevronDown } from 'lucide-react'
import { Button } from '@/components/ui/button'

const languages = [
  { code: 'en', name: 'English', flag: '🇬🇧' },
  { code: 'sw', name: 'Kiswahili', flag: '🇰🇪' },
]

export function LanguageSelector() {
  const [selectedLanguage, setSelectedLanguage] = useState(languages[0])
  const [isOpen, setIsOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    // Load saved language from localStorage
    const savedLang = localStorage.getItem('language')
    if (savedLang) {
      const lang = languages.find(l => l.code === savedLang)
      if (lang) setSelectedLanguage(lang)
    }
  }, [])

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleLanguageChange = (language: typeof languages[0]) => {
    setSelectedLanguage(language)
    localStorage.setItem('language', language.code)
    setIsOpen(false)
    // Here you would typically trigger a translation update
  }

  return (
    <div className="relative" ref={dropdownRef}>
      <Button
        variant="ghost"
        size="sm"
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 h-9 px-3 rounded-full hover:bg-green-100 dark:hover:bg-green-900/30 transition-colors"
        aria-label="Select language"
      >
        <Globe className="h-4 w-4 text-gray-700 dark:text-gray-300" />
        <span className="text-sm font-medium text-gray-700 dark:text-gray-300 hidden sm:inline">
          {selectedLanguage.code.toUpperCase()}
        </span>
        <ChevronDown className={`h-3 w-3 text-gray-700 dark:text-gray-300 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`} />
      </Button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div className="absolute right-0 mt-2 w-48 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 py-1 z-50 animate-in fade-in slide-in-from-top-2 duration-200">
          {languages.map((language) => (
            <button
              key={language.code}
              onClick={() => handleLanguageChange(language)}
              className="w-full flex items-center justify-between px-4 py-2.5 text-sm hover:bg-green-50 dark:hover:bg-green-900/20 transition-colors"
            >
              <div className="flex items-center gap-3">
                <span className="text-xl">{language.flag}</span>
                <span className="text-gray-700 dark:text-gray-300 font-medium">
                  {language.name}
                </span>
              </div>
              {selectedLanguage.code === language.code && (
                <Check className="h-4 w-4 text-green-600 dark:text-green-400" />
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

