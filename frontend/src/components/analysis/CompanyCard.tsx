import type { Company } from '../../types';
import { timestampToSeconds } from '../../utils/validation';

interface CompanyCardProps {
    company: Company;
    videoUrl: string;
}

export function CompanyCard({ company, videoUrl }: CompanyCardProps) {
    const { name, ticker, description, context, sentiment, timestamp } = company;

    // Sentiment styling
    const sentimentConfig = {
        positive: {
            color: 'text-green-400',
            bg: 'bg-green-400/10',
            label: 'Bullish',
            icon: '↗️',
        },
        negative: {
            color: 'text-red-400',
            bg: 'bg-red-400/10',
            label: 'Bearish',
            icon: '↘️',
        },
        neutral: {
            color: 'text-gray-400',
            bg: 'bg-gray-400/10',
            label: 'Neutral',
            icon: '➖',
        },
    };

    const config = sentimentConfig[sentiment] || sentimentConfig.neutral;

    return (
        <div className="glass-card p-5 transition-transform hover:scale-[1.01]">
            {/* Header */}
            <div className="flex justify-between items-start mb-3">
                <div className="flex items-center gap-3">
                    <h4 className="text-lg font-semibold text-white">{name}</h4>
                    {ticker && (
                        <span className="px-2 py-0.5 bg-white/10 rounded text-xs font-medium text-gray-300">
                            {ticker}
                        </span>
                    )}
                </div>
                <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold uppercase ${config.bg} ${config.color}`}>
                    {config.icon} {config.label}
                </span>
            </div>

            {/* Description */}
            <p className="text-gray-300 mb-3 leading-relaxed">{description}</p>

            {/* Footer: Context + Timestamp */}
            <div className="flex justify-between items-end pt-3 border-t border-white/10">
                {context ? (
                    <p className="text-sm italic text-gray-500 max-w-[85%]">"{context}"</p>
                ) : (
                    <div />
                )}
                {timestamp && (
                    <a
                        href={`${videoUrl}&t=${timestampToSeconds(timestamp)}s`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-1 text-sm text-accent-primary hover:underline"
                    >
                        ⏱ {timestamp}
                    </a>
                )}
            </div>
        </div>
    );
}
