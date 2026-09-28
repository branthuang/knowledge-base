import React from 'react';
import { Sparkles, Database, Globe, Bot } from 'lucide-react';
import { SearchMode } from '@/lib/types';

interface ModeSelectorProps {
  currentMode: SearchMode;
  onModeChange: (mode: SearchMode) => void;
}

const MODES: {
  id: SearchMode;
  label: string;
  desc: string;
  icon: React.ElementType;
}[] = [
  {
    id: 'knowledge_first',
    label: '知识优先',
    desc: '本地优先，充分时仅用本地，不足时公网补充',
    icon: Database,
  },
  {
    id: 'knowledge_only',
    label: '仅知识库',
    desc: '严格仅查本地库，绝不发起外部请求',
    icon: Sparkles,
  },
  {
    id: 'external_supplement',
    label: '外部补充',
    desc: '强制本地与外部公网补充综合回答',
    icon: Globe,
  },
  {
    id: 'direct_ai',
    label: '直接 AI',
    desc: '直接向 AI 提问，侧边展示关联本地知识',
    icon: Bot,
  },
];

export const ModeSelector: React.FC<ModeSelectorProps> = ({
  currentMode,
  onModeChange,
}) => {
  return (
    <div className="flex items-center gap-1.5 p-1 bg-slate-100 rounded-xl border border-slate-200 w-full sm:w-auto">
      {MODES.map((mode) => {
        const Icon = mode.icon;
        const isActive = currentMode === mode.id;

        return (
          <button
            key={mode.id}
            type="button"
            onClick={() => onModeChange(mode.id)}
            title={mode.desc}
            className={`flex-1 sm:flex-initial flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              isActive
                ? 'bg-white text-blue-600 shadow-xs border border-slate-200/80 font-semibold'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/60'
            }`}
          >
            <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-blue-600' : 'text-slate-400'}`} />
            <span>{mode.label}</span>
          </button>
        );
      })}
    </div>
  );
};
