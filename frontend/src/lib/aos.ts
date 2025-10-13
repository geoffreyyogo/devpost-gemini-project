/**
 * AOS (Animate On Scroll) Configuration
 * Simple scroll animations for elements
 */

'use client'

import { useEffect } from 'react'

export function useAOSInit() {
  useEffect(() => {
    // Simple intersection observer-based animation
    const observerOptions = {
      threshold: 0.1,
      rootMargin: '0px 0px -100px 0px'
    }

    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('aos-animate')
        }
      })
    }, observerOptions)

    // Observe all elements with data-aos attribute
    const elements = document.querySelectorAll('[data-aos]')
    elements.forEach((el) => observer.observe(el))

    return () => {
      elements.forEach((el) => observer.unobserve(el))
    }
  }, [])
}

