import type { AnalysisResult } from '../../types';
import { CompanyCard } from './CompanyCard';
import { WatchlistCard } from './WatchlistCard';
import { Button } from '../ui';

interface AnalysisResultsProps {
    result: AnalysisResult;
    onAnalyzeAnother: () => void;
}

export function AnalysisResults({ result, onAnalyzeAnother }: AnalysisResultsProps) {
    const { companies, watchlist, summary, video_url, cached } = result;

    return (
        <div className="space-y-8 animate-in fade-in duration-500">
            {/* Video Link */}
            <div className="flex items-center gap-4">
                <a
                    href={video_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="btn-secondary inline-flex items-center gap-2"
                >
                    <span className="text-red-500 text-xl">▶</span>
                    Watch on YouTube
                </a>
                {cached && (
                    <span className="text-xs text-gray-500 bg-white/5 px-2 py-1 rounded inline-flex items-center gap-1">
                        ⚡ Cached
                    </span>
                )}
                {result.model && (
                    <span className="text-xs text-gray-400 bg-white/5 px-2 py-1 rounded inline-flex items-center gap-1 border border-white/10">
                        🤖 AI: {result.model}
                    </span>
                )}
            </div>

            {/* Summary */}
            {summary && (
                <div className="glass-card p-6 border border-accent-primary/30 bg-accent-primary/5">
                    <div className="flex items-center gap-3 mb-3">
                        <span className="text-2xl">📝</span>
                        <h3 className="text-xl font-semibold text-accent-primary">Executive Summary</h3>
                    </div>
                    <p className="text-gray-300 leading-relaxed text-lg">{summary}</p>
                </div>
            )}

            {/* Watchlist */}
            {watchlist.length > 0 && (
                <section>
                    <div className="flex items-center gap-3 mb-4">
                        <span className="text-2xl">⭐</span>
                        <h3 className="text-xl font-semibold text-green-400">
                            Presenter's Watchlist ({watchlist.length})
                        </h3>
                    </div>
                    <div className="grid gap-4">
                        {watchlist.map((item, index) => (
                            <WatchlistCard key={index} item={item} videoUrl={video_url} />
                        ))}
                    </div>
                </section>
            )}

            {/* Companies */}
            <section>
                <div className="flex items-center gap-3 mb-4">
                    <span className="text-2xl">📈</span>
                    <h3 className="text-xl font-semibold text-white">
                        All Mentions ({companies.length})
                    </h3>
                </div>
                {companies.length === 0 ? (
                    <div className="glass-card p-8 text-center text-gray-500">
                        No company mentions found in this video.
                    </div>
                ) : (
                    <div className="grid gap-4">
                        {companies.map((company, index) => (
                            <CompanyCard key={index} company={company} videoUrl={video_url} />
                        ))}
                    </div>
                )}
            </section>

            {/* Analyze Another Button */}
            <div className="pt-4">
                <Button variant="secondary" onClick={onAnalyzeAnother}>
                    Analyze Another Video
                </Button>
            </div>
        </div>
    );
}
