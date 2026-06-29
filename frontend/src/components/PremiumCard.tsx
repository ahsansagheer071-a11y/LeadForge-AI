import { cn } from '@/utils'
import type { ReactNode } from 'react'

interface PremiumCardProps {
  children: ReactNode
  className?: string
  innerClassName?: string
}

/** LeadForge signature card — subtle rotating RGB border (KPI + AI Insights only). */
export default function PremiumCard({ children, className, innerClassName }: PremiumCardProps) {
  return (
    <div className={cn('premium-card', className)}>
      <div className={cn('premium-card__inner', innerClassName)}>{children}</div>
    </div>
  )
}
