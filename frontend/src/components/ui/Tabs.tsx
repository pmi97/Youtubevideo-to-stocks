import { ReactNode } from 'react';

interface Tab {
    id: string;
    label: string;
    icon?: string;
}

interface TabsProps {
    tabs: Tab[];
    activeTab: string;
    onTabChange: (tabId: string) => void;
    children: ReactNode;
}

export function Tabs({ tabs, activeTab, onTabChange, children }: TabsProps) {
    return (
        <div>
            <div className="flex border-b border-white/10 mb-6">
                {tabs.map((tab) => (
                    <button
                        key={tab.id}
                        onClick={() => onTabChange(tab.id)}
                        className={`
              flex items-center gap-2 px-6 py-3 text-sm font-medium transition-all
              border-b-2 -mb-[1px]
              ${activeTab === tab.id
                                ? 'border-accent-primary text-white'
                                : 'border-transparent text-gray-400 hover:text-white hover:border-white/30'
                            }
            `}
                    >
                        {tab.icon && <span>{tab.icon}</span>}
                        {tab.label}
                    </button>
                ))}
            </div>
            {children}
        </div>
    );
}

interface TabPanelProps {
    id: string;
    activeTab: string;
    children: ReactNode;
}

export function TabPanel({ id, activeTab, children }: TabPanelProps) {
    if (id !== activeTab) return null;
    return <div>{children}</div>;
}
