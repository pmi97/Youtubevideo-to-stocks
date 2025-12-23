import { useState, FormEvent } from 'react';
import { Button, Input, Select } from '../ui';
import { AnalysisResults } from './AnalysisResults';
import { analyzeVideo } from '../../services/api';
import { isValidVideoUrl, isValidEmail } from '../../utils/validation';
import type { AnalysisResult } from '../../types';

const LANGUAGES = [
    { value: 'en', label: 'English' },
    { value: 'es', label: 'Español' },
    { value: 'sv', label: 'Svenska' },
];

export function AnalysisForm() {
    const [videoUrl, setVideoUrl] = useState('');
    const [email, setEmail] = useState('');
    const [language, setLanguage] = useState('en');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [result, setResult] = useState<AnalysisResult | null>(null);

    const handleSubmit = async (e: FormEvent) => {
        e.preventDefault();
        setError('');

        // Validation
        if (!isValidVideoUrl(videoUrl)) {
            setError('Please enter a valid YouTube video URL or video ID');
            return;
        }

        if (email && !isValidEmail(email)) {
            setError('Please enter a valid email address');
            return;
        }

        setLoading(true);

        try {
            const data = await analyzeVideo({
                video_url: videoUrl.trim(),
                email: email || undefined,
                language,
            });
            setResult(data);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Something went wrong');
        } finally {
            setLoading(false);
        }
    };

    const handleReset = () => {
        setResult(null);
        setVideoUrl('');
        setError('');
    };

    // Show results if we have them
    if (result) {
        return <AnalysisResults result={result} onAnalyzeAnother={handleReset} />;
    }

    return (
        <form onSubmit={handleSubmit} className="space-y-6">
            <Input
                label="YouTube Video URL"
                icon="🔗"
                placeholder="https://youtube.com/watch?v=... or video ID"
                hint="Paste any YouTube video URL to analyze it"
                value={videoUrl}
                onChange={(e) => setVideoUrl(e.target.value)}
                required
            />

            <Input
                label="Email (optional)"
                icon="✉️"
                type="email"
                placeholder="you@example.com"
                hint="Get the analysis sent to your inbox"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
            />

            <Select
                label="Language"
                icon="🌐"
                options={LANGUAGES}
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
            />

            {error && (
                <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-xl text-red-400 text-sm">
                    {error}
                </div>
            )}

            <Button type="submit" loading={loading} className="w-full">
                Analyze Video
            </Button>
        </form>
    );
}
