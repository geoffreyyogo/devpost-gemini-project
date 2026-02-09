/**
 * CTA Section Component
 * Call-to-action with rotating background images
 */

'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Rocket, Smartphone, CheckCircle } from 'lucide-react'

const backgroundImages = [
  {
    url: 'https://images.unsplash.com/photo-1625246333195-78d9c38ad449?w=1920&q=85',
    alt: 'Maize fields in Rift Valley',
    credit: 'Unsplash'
  },
  {
    url: 'https://www.greenlife.co.ke/wp-content/uploads/2022/04/Coffee-Feeding-Greenlife.jpg',
    alt: 'Coffee blooms in Central Kenya',
    credit: 'Greenlife'
  },
  {
    url: 'https://images.unsplash.com/photo-1500382017468-9049fed747ef?w=1920&q=85',
    alt: 'Tea plantations in Kericho',
    credit: 'Unsplash'
  },
  {
    url: 'https://images.unsplash.com/photo-1574943320219-553eb213f72d?w=1920&q=85',
    alt: 'Diverse crops thriving',
    credit: 'Unsplash'
  },
  {
    url: 'https://images.unsplash.com/photo-1523348837708-15d4a09cfac2?w=1920&q=85',
    alt: 'Kenyan farmers in the field',
    credit: 'Unsplash'
  }
]

export function CTASection() {
  const [currentImageIndex, setCurrentImageIndex] = useState(0)

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentImageIndex((prevIndex) => 
        (prevIndex + 1) % backgroundImages.length
      )
    }, 10000) // 10 seconds

    return () => clearInterval(interval)
  }, [])

  return (
    <section className="relative overflow-hidden py-16 md:py-24 min-h-[600px] bg-gradient-to-br from-green-600 via-green-700 to-green-800">
      {/* Rotating Background Images using regular img tags */}
      {backgroundImages.map((image, index) => (
        <div
          key={index}
          className={`absolute inset-0 z-0 transition-opacity duration-1000 ${
            index === currentImageIndex ? 'opacity-100' : 'opacity-0'
          }`}
        >
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={image.url}
            alt={image.alt}
            className="absolute inset-0 w-full h-full object-cover animate-parallax"
            loading={index === 0 ? "eager" : "lazy"}
            onError={(e) => {
              console.error(`Failed to load image ${index + 1}:`, image.url)
              e.currentTarget.style.display = 'none'
            }}
          />
          {/* Dark overlay for text readability */}
          <div className="absolute inset-0 bg-gradient-to-br from-black/70 via-green-900/60 to-black/70 z-10" />
        </div>
      ))}

      {/* Decorative Elements */}
      <div className="absolute inset-0 opacity-10 z-20 pointer-events-none">
        <div className="absolute top-10 left-10 w-64 h-64 bg-white rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute bottom-10 right-10 w-96 h-96 bg-green-400 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1s' }}></div>
      </div>

      <div className="container mx-auto px-4 relative z-30">
        <div className="max-w-4xl mx-auto text-center text-white">
          {/* Heading */}
          <div className="mb-8 md:mb-12" data-aos="fade-down">
            <div className="inline-block px-6 py-2 bg-white/20 backdrop-blur-sm rounded-full text-sm font-semibold mb-4 border border-white/30">
              🚀 Join The Future of Farming
            </div>
            <h2 className="text-3xl md:text-5xl lg:text-6xl font-bold mb-4 md:mb-6 drop-shadow-2xl">
              Ready to Optimize Your Harvest?
            </h2>
            <p className="text-lg md:text-xl lg:text-2xl opacity-95 leading-relaxed drop-shadow-lg">
              Join thousands of Kenyan farmers using Smart Shamba to increase yields and reduce crop loss
            </p>
          </div>

          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row gap-4 md:gap-6 justify-center items-center" data-aos="fade-up">
            <Link href="/register" className="w-full sm:w-auto">
              <Button 
                size="lg" 
                className="w-full sm:w-auto bg-white text-green-700 hover:bg-green-50 hover:scale-105 transition-all duration-300 text-base md:text-lg px-8 md:px-12 py-6 md:py-7 rounded-full shadow-2xl font-bold group"
              >
                <Rocket className="mr-2 h-5 w-5 group-hover:rotate-12 transition-transform" />
                Register Now - It&apos;s Free
              </Button>
            </Link>
            <Link href="tel:*384*42434#" className="w-full sm:w-auto">
              <Button 
                size="lg" 
                className="w-full sm:w-auto bg-green-700/80 text-white border-2 border-white hover:bg-white hover:text-green-700 transition-all duration-300 text-base md:text-lg px-8 md:px-12 py-6 md:py-7 rounded-full shadow-2xl hover:scale-105 font-bold backdrop-blur-sm group"
              >
                <Smartphone className="mr-2 h-5 w-5 group-hover:animate-bounce" />
                USSD: *384*42434#
              </Button>
            </Link>
          </div>

          {/* Trust Indicators */}
          <div className="mt-12 md:mt-16 pt-8 border-t border-white/20" data-aos="fade-up" data-aos-delay="200">
            <div className="flex flex-wrap justify-center items-center gap-8 text-sm md:text-base">
              <div className="flex items-center gap-2">
                <CheckCircle className="h-5 w-5 text-green-200" />
                <span className="font-semibold drop-shadow-md">100% Free</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle className="h-5 w-5 text-green-200" />
                <span className="font-semibold drop-shadow-md">Works on ANY Phone</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle className="h-5 w-5 text-green-200" />
                <span className="font-semibold drop-shadow-md">Real-time Alerts</span>
              </div>
            </div>
          </div>

          {/* Image Attribution (small, subtle) */}
          <div className="mt-8 text-xs text-white/60 drop-shadow-sm">
            Photo: {backgroundImages[currentImageIndex].credit}
          </div>
        </div>
      </div>

      {/* Progress Indicators */}
      <div className="absolute bottom-8 left-1/2 transform -translate-x-1/2 flex gap-2 z-30">
        {backgroundImages.map((_, index) => (
          <button
            key={index}
            onClick={() => setCurrentImageIndex(index)}
            className={`progress-indicator w-2 h-2 rounded-full transition-all duration-300 ${
              index === currentImageIndex 
                ? 'bg-white w-8' 
                : 'bg-white/50 hover:bg-white/75'
            }`}
            aria-label={`Go to image ${index + 1}`}
          />
        ))}
      </div>
    </section>
  )
}

