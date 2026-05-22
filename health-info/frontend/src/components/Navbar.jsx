import { NavLink } from 'react-router-dom'
import { LayoutDashboard, UtensilsCrossed, Dumbbell, ChefHat, Settings } from 'lucide-react'

const links = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/log', label: 'Log Meal', icon: UtensilsCrossed },
  { to: '/activity', label: 'Activity', icon: Dumbbell },
  { to: '/recipes', label: 'Recipes', icon: ChefHat },
  { to: '/settings', label: 'Settings', icon: Settings },
]

export default function Navbar() {
  return (
    <nav className="border-b border-border bg-bg-card sticky top-0 z-50">
      <div className="max-w-5xl mx-auto px-4 flex items-center justify-between h-14">
        <span className="font-heading font-bold text-xl text-accent tracking-tight">CalorIQ</span>
        <div className="flex gap-1">
          {links.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-bg-elevated text-accent'
                    : 'text-text-muted hover:text-text-primary hover:bg-bg-elevated'
                }`
              }
            >
              <Icon size={15} />
              <span className="hidden sm:inline">{label}</span>
            </NavLink>
          ))}
        </div>
      </div>
    </nav>
  )
}
