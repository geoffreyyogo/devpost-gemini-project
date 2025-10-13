/**
 * Counter Animation Hook
 * Animates numbers from 0 to target value when element comes into view
 */

'use client'

import { useEffect, useRef, useState } from 'react'

interface UseCountAnimationOptions {
  start?: number
  end: number
  duration?: number
  suffix?: string
  prefix?: string
}

export function useCountAnimation({
  start = 0,
  end,
  duration = 2000,
  suffix = '',
  prefix = ''
}: UseCountAnimationOptions) {
  const [count, setCount] = useState(start)
  const [hasAnimated, setHasAnimated] = useState(false)
  const elementRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting && !hasAnimated) {
            setHasAnimated(true)
            
            const startTime = Date.now()
            const startValue = start
            const endValue = end
            const totalDuration = duration

            const animate = () => {
              const now = Date.now()
              const elapsed = now - startTime
              const progress = Math.min(elapsed / totalDuration, 1)

              // Easing function (ease-out)
              const easeOut = 1 - Math.pow(1 - progress, 3)
              const currentCount = Math.floor(startValue + (endValue - startValue) * easeOut)

              setCount(currentCount)

              if (progress < 1) {
                requestAnimationFrame(animate)
              }
            }

            requestAnimationFrame(animate)
          }
        })
      },
      { threshold: 0.3 } // Trigger when 30% visible
    )

    if (elementRef.current) {
      observer.observe(elementRef.current)
    }

    return () => {
      if (elementRef.current) {
        observer.unobserve(elementRef.current)
      }
    }
  }, [start, end, duration, hasAnimated])

  return {
    ref: elementRef,
    displayValue: `${prefix}${count.toLocaleString()}${suffix}`
  }
}

