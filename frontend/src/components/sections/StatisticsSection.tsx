/**
 * Statistics Section Component
 * Displays key metrics with animated counters
 */

'use client'

import { Users, MapPin, Bell, Satellite } from 'lucide-react'
import { useCountAnimation } from '@/hooks/useCountAnimation'

function StatCard({ 
  icon: Icon, 
  end, 
  suffix = '', 
  prefix = '', 
  label,
  color = 'text-green-600'
}: { 
  icon: any
  end: number
  suffix?: string
  prefix?: string
  label: string
  color?: string
}) {
  const { ref, displayValue } = useCountAnimation({ end, suffix, prefix, duration: 2500 })

  return (
    <div 
      className="space-y-4 group hover:scale-105 transition-transform duration-500 cursor-default"
      data-aos="fade-up"
    >
      <div className="flex justify-center">
        <div className={`p-4 md:p-5 bg-green-50 dark:bg-green-950 rounded-full group-hover:scale-110 group-hover:shadow-xl transition-all duration-500 ${color.replace('text', 'shadow')}/20`}>
          <Icon className={`h-10 w-10 md:h-12 md:w-12 ${color} group-hover:animate-pulse`} />
        </div>
      </div>
      <div 
        ref={ref}
        className={`text-4xl md:text-5xl lg:text-6xl font-bold ${color} group-hover:scale-110 transition-transform duration-300`}
      >
        {displayValue}
      </div>
      <div className="text-base md:text-lg text-gray-700 dark:text-gray-300 font-medium px-2">
        {label}
      </div>
    </div>
  )
}

export function StatisticsSection() {
  return (
    <section className="container mx-auto px-4 py-16 md:py-24">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8 md:gap-12 text-center">
        <StatCard
          icon={Users}
          end={5000}
          suffix="+"
          label="Farmers Registered"
          color="text-green-600"
        />
        <StatCard
          icon={MapPin}
          end={47}
          label="Counties Covered"
          color="text-blue-600"
        />
        <StatCard
          icon={Bell}
          end={50000}
          suffix="+"
          label="Alerts Sent"
          color="text-orange-600"
        />
        <div 
          className="space-y-4 group hover:scale-105 transition-transform duration-500 cursor-default"
          data-aos="fade-up"
        >
          <div className="flex justify-center">
            <div className="p-4 md:p-5 bg-green-50 dark:bg-green-950 rounded-full group-hover:scale-110 group-hover:shadow-xl transition-all duration-500">
              <Satellite className="h-10 w-10 md:h-12 md:w-12 text-purple-600 group-hover:animate-pulse" />
            </div>
          </div>
          <div className="text-4xl md:text-5xl lg:text-6xl font-bold text-purple-600 group-hover:scale-110 transition-transform duration-300">
            Daily
          </div>
          <div className="text-base md:text-lg text-gray-700 dark:text-gray-300 font-medium px-2">
            Satellite Updates
          </div>
        </div>
      </div>
    </section>
  )
}

