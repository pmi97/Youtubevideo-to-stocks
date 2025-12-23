import type { WatchlistItem } from '../../types';
import { timestampToSeconds } from '../../utils/validation';

interface WatchlistCardProps {
    item: WatchlistItem;
    videoUrl: string;
}

export function WatchlistCard({ item, videoUrl }: WatchlistCardProps) {
    const { name, ticker, reason, timestamp } = item;

    return (
        <div className="glass-card p-5 border-l-4 border-l-green-500 bg-green-500/5">
            {/* Header */}
            <div className="flex justify-between items-start mb-3">
                <div className="flex items-center gap-3">
                    <h4 className="text-lg font-semibold text-white">{name}</h4>
                    {ticker && (
                        <span className="px-2 py-0.5 bg-green-500/20 text-green-400 rounded text-xs font-semibold">
                            {ticker}
                        </span>
                    )}
                </div>
                {timestamp && (
                    <a
                        href={`${videoUrl}&t=${timestampToSeconds(timestamp)}s`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-1 px-2 py-1 bg-green-500/10 rounded text-sm font-medium text-green-400 hover:bg-green-500/20 transition-colors"
                    >
                        ⏱ {timestamp}
                    </a>
                )}
            </div>

            {/* Reason */}
            <p className="text-gray-300">
                <span className="font-medium text-green-400">Why:</span> {reason}
            </p>
        </div>
    );
}
