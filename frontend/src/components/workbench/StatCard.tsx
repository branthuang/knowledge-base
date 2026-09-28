import React from 'react';
import { LucideIcon } from 'lucide-react';

interface StatCardProps {
  title: string;
  value: number | string;
  description?: string;
  icon: LucideIcon;
  colorVariant?: 'blue' | 'indigo' | 'emerald' | 'amber' | 'purple';
}

const colorStyles = {
  blue: {
    bg: 'bg-blue-50 text-blue-600',
    border: 'border-blue-100',
    shadow: 'hover:shadow-blue-500/10',
  },
  indigo: {
    bg: 'bg-indigo-50 text-indigo-600',
    border: 'border-indigo-100',
    shadow: 'hover:shadow-indigo-500/10',
  },
  emerald: {
    bg: 'bg-emerald-50 text-emerald-600',
    border: 'border-emerald-100',
    shadow: 'hover:shadow-emerald-500/10',
  },
  amber: {
    bg: 'bg-amber-50 text-amber-600',
    border: 'border-amber-100',
    shadow: 'hover:shadow-amber-500/10',
  },
  purple: {
    bg: 'bg-purple-50 text-purple-600',
    border: 'border-purple-100',
    shadow: 'hover:shadow-purple-500/10',
  },
};

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  description,
  icon: Icon,
  colorVariant = 'blue',
}) => {
  const currentStyle = colorStyles[colorVariant] || colorStyles.blue;

  return (
    <div
      className={`bg-white border ${currentStyle.border} rounded-xl p-5 shadow-sm transition-all duration-200 ${currentStyle.shadow} hover:-translate-y-0.5`}
    >
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold text-slate-500 uppercase tracking-wide">
          {title}
        </span>
        <div className={`w-9 h-9 rounded-lg flex items-center justify-center ${currentStyle.bg}`}>
          <Icon className="w-5 h-5" />
        </div>
      </div>

      <div className="mt-3">
        <div className="text-2xl font-bold text-slate-800 tracking-tight">
          {typeof value === 'number' ? value.toLocaleString() : value}
        </div>
        {description && (
          <p className="mt-1 text-xs text-slate-400">
            {description}
          </p>
        )}
      </div>
    </div>
  );
};
