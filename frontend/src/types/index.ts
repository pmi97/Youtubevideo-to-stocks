// API Response Types

export interface Company {
    name: string;
    ticker?: string;
    description: string;
    context?: string;
    sentiment: 'positive' | 'negative' | 'neutral';
    timestamp?: string;
}

export interface WatchlistItem {
    name: string;
    ticker?: string;
    reason: string;
    timestamp?: string;
}

export interface AnalysisResult {
    companies: Company[];
    watchlist: WatchlistItem[];
    summary: string;
    video_url: string;
    video_title?: string;
    cached?: boolean;
    model?: string;
}

export interface AnalyzeRequest {
    video_url: string;
    email?: string;
    language: string;
}

export interface Channel {
    url: string;
}

export interface SubscribeRequest {
    email: string;
    language: string;
    channels: Channel[];
}

export interface SubscribeResponse {
    message: string;
    subscribed_channels: number;
}

// Tab Types
export type TabType = 'analyze' | 'subscribe';
