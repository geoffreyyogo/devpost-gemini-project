'use client'

import { useState, useEffect } from 'react'
import { ChevronLeft, ChevronRight } from 'lucide-react'
import Image from 'next/image'

interface CarouselImage {
  url: string
  caption: string
}

const images: CarouselImage[] = [
  {
    url: 'https://images.unsplash.com/photo-1625246333195-78d9c38ad449?w=1200',
    caption: '🌾 Maize fields in Rift Valley - Track bloom timing for optimal harvest'
  },
  {
    url: 'https://www.greenlife.co.ke/wp-content/uploads/2022/04/Coffee-Feeding-Greenlife.jpg',
    caption: '☕ Coffee blooms in Central Kenya - Premium Grade A quality'
  },
  {
    url: 'https://images.unsplash.com/photo-1500382017468-9049fed747ef?w=1200',
    caption: '🍃 Tea plantations in Kericho - Year-round monitoring'
  },
  {
    url: 'https://images.unsplash.com/photo-1574943320219-553eb213f72d?w=1200',
    caption: '🌻 Diverse crops thriving with NASA satellite insights'
  },
  {
    url: 'https://images.unsplash.com/photo-1523348837708-15d4a09cfac2?w=1200',
    caption: '👨‍🌾 Kenyan farmers - The heart of Smart Shamba'
  }
]

export function AgriculturalCarousel() {
  const [currentIndex, setCurrentIndex] = useState(0)
  const [isAutoPlaying, setIsAutoPlaying] = useState(true)
  const [isTransitioning, setIsTransitioning] = useState(false)

  // Auto-rotation every 6 seconds for better viewing experience
  useEffect(() => {
    if (!isAutoPlaying) return

    const interval = setInterval(() => {
      setIsTransitioning(true)
      setTimeout(() => {
        setCurrentIndex((prevIndex) => (prevIndex + 1) % images.length)
        setIsTransitioning(false)
      }, 150)
    }, 6000)

    return () => clearInterval(interval)
  }, [isAutoPlaying])

  const goToPrevious = () => {
    if (isTransitioning) return
    setIsAutoPlaying(false)
    setIsTransitioning(true)
    setTimeout(() => {
      setCurrentIndex((prevIndex) => (prevIndex - 1 + images.length) % images.length)
      setIsTransitioning(false)
    }, 150)
  }

  const goToNext = () => {
    if (isTransitioning) return
    setIsAutoPlaying(false)
    setIsTransitioning(true)
    setTimeout(() => {
      setCurrentIndex((prevIndex) => (prevIndex + 1) % images.length)
      setIsTransitioning(false)
    }, 150)
  }

  const goToSlide = (index: number) => {
    if (isTransitioning || index === currentIndex) return
    setIsAutoPlaying(false)
    setIsTransitioning(true)
    setTimeout(() => {
      setCurrentIndex(index)
      setIsTransitioning(false)
    }, 150)
  }

  // Resume auto-play after 8 seconds of manual interaction
  useEffect(() => {
    if (!isAutoPlaying) {
      const timer = setTimeout(() => {
        setIsAutoPlaying(true)
      }, 8000)
      return () => clearTimeout(timer)
    }
  }, [isAutoPlaying])

  return (
    <div className="relative group">
      {/* Main carousel container */}
      <div className="relative overflow-hidden rounded-2xl md:rounded-3xl shadow-2xl bg-white dark:bg-gray-900">
        {/* Image container */}
        <div className="relative h-[300px] sm:h-[400px] md:h-[500px] lg:h-[600px] overflow-hidden">
          <Image
            src={images[currentIndex].url}
            alt={images[currentIndex].caption}
            fill
            className={`object-cover transition-all duration-500 ease-in-out ${
              isTransitioning ? 'opacity-0 scale-105' : 'opacity-100 scale-100'
            }`}
            sizes="(max-width: 768px) 100vw, (max-width: 1200px) 80vw, 1200px"
            priority={currentIndex === 0}
          />
          
          {/* Gradient overlay for text readability */}
          <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-transparent to-transparent" />
          
          {/* Caption */}
          <div className="absolute bottom-0 left-0 right-0 p-4 md:p-6 lg:p-8">
            <p className={`text-white text-sm sm:text-base md:text-lg lg:text-xl font-semibold text-center leading-relaxed drop-shadow-lg transition-all duration-500 ease-in-out ${
              isTransitioning ? 'opacity-0 translate-y-4' : 'opacity-100 translate-y-0'
            }`}>
              {images[currentIndex].caption}
            </p>
          </div>
        </div>

        {/* Navigation arrows */}
        <button
          onClick={goToPrevious}
          className="absolute left-4 top-1/2 -translate-y-1/2 bg-white/20 hover:bg-white/40 backdrop-blur-sm text-white p-2 md:p-3 rounded-full transition-all duration-300 hover:scale-110 opacity-0 group-hover:opacity-100 shadow-lg"
          aria-label="Previous image"
        >
          <ChevronLeft className="h-5 w-5 md:h-6 md:w-6" />
        </button>

        <button
          onClick={goToNext}
          className="absolute right-4 top-1/2 -translate-y-1/2 bg-white/20 hover:bg-white/40 backdrop-blur-sm text-white p-2 md:p-3 rounded-full transition-all duration-300 hover:scale-110 opacity-0 group-hover:opacity-100 shadow-lg"
          aria-label="Next image"
        >
          <ChevronRight className="h-5 w-5 md:h-6 md:w-6" />
        </button>

        {/* Progress indicator */}
        <div className="absolute top-4 right-4 bg-black/30 backdrop-blur-sm text-white px-3 py-1 rounded-full text-xs font-medium">
          {currentIndex + 1} / {images.length}
        </div>
      </div>

      {/* Dot indicators */}
      <div className="flex justify-center mt-6 space-x-2">
        {images.map((_, index) => (
          <button
            key={index}
            onClick={() => goToSlide(index)}
            className={`w-3 h-3 md:w-4 md:h-4 rounded-full transition-all duration-300 ${
              index === currentIndex
                ? 'bg-green-600 scale-125 shadow-lg'
                : 'bg-gray-300 hover:bg-gray-400 dark:bg-gray-600 dark:hover:bg-gray-500'
            }`}
            aria-label={`Go to slide ${index + 1}`}
          />
        ))}
      </div>

      {/* Auto-play indicator */}
      <div className="flex justify-center mt-4">
        <button
          onClick={() => setIsAutoPlaying(!isAutoPlaying)}
          className={`px-4 py-2 rounded-full text-sm font-medium transition-all duration-300 ${
            isAutoPlaying
              ? 'bg-green-100 text-green-700 hover:bg-green-200 dark:bg-green-900/30 dark:text-green-400'
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-400'
          }`}
        >
          {isAutoPlaying ? '⏸️ Auto-playing' : '▶️ Resume auto-play'}
        </button>
      </div>
    </div>
  )
}
