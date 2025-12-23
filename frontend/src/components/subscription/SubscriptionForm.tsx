import { useState, FormEvent } from 'react';
import { Button, Input, Select } from '../ui';
import { subscribe } from '../../services/api';
import { isValidChannelUrl, isValidEmail } from '../../utils/validation';

const LANGUAGES = [
    { value: 'en', label: 'English' },
    { value: 'es', label: 'Español' },
    { value: 'sv', label: 'Svenska' },
];

const MAX_CHANNELS = 20;

type Status = 'idle' | 'loading' | 'success' | 'error';

export function SubscriptionForm() {
    const [email, setEmail] = useState('');
    const [language, setLanguage] = useState('en');
    const [channels, setChannels] = useState(['']);
    const [status, setStatus] = useState<Status>('idle');
    const [error, setError] = useState('');

    const addChannel = () => {
        if (channels.length >= MAX_CHANNELS) {
            setError(`Maximum ${MAX_CHANNELS} channels allowed`);
            return;
        }
        setChannels([...channels, '']);
    };

    const removeChannel = (index: number) => {
        if (channels.length <= 1) return;
        setChannels(channels.filter((_, i) => i !== index));
    };

    const updateChannel = (index: number, value: string) => {
        const updated = [...channels];
        updated[index] = value;
        setChannels(updated);
    };

    const handleSubmit = async (e: FormEvent) => {
        e.preventDefault();
        setError('');

        // Filter empty channels
        const validChannels = channels.filter((c) => c.trim());

        if (validChannels.length === 0) {
            setError('Please add at least one channel');
            return;
        }

        if (!isValidEmail(email) || !email) {
            setError('Please enter a valid email address');
            return;
        }

        // Validate each channel
        for (const channel of validChannels) {
            if (!isValidChannelUrl(channel)) {
                setError(`Invalid channel: "${channel}". Use @username or YouTube URL.`);
                return;
            }
        }

        setStatus('loading');

        try {
            await subscribe({
                email,
                language,
                channels: validChannels.map((url) => ({ url })),
            });
            setStatus('success');
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Something went wrong');
            setStatus('error');
        }
    };

    const handleReset = () => {
        setStatus('idle');
        setEmail('');
        setChannels(['']);
        setError('');
    };

    // Success state
    if (status === 'success') {
        return (
            <div className="text-center py-8 space-y-4 animate-in fade-in duration-500">
                <div className="w-16 h-16 mx-auto bg-green-500/20 rounded-full flex items-center justify-center">
                    <span className="text-3xl">✓</span>
                </div>
                <h3 className="text-xl font-semibold text-white">You're all set!</h3>
                <p className="text-gray-400">
                    We'll analyze new videos from your subscribed channels and send you detailed reports.
                </p>
                <Button variant="secondary" onClick={handleReset}>
                    Subscribe to More Channels
                </Button>
            </div>
        );
    }

    return (
        <form onSubmit={handleSubmit} className="space-y-6">
            <Input
                label="Your Email"
                icon="✉️"
                type="email"
                placeholder="you@example.com"
                hint="We'll send analysis reports to this email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
            />

            <Select
                label="Language"
                icon="🌐"
                options={LANGUAGES}
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
            />

            {/* Channels */}
            <div className="space-y-2">
                <label className="flex items-center gap-2 text-sm font-medium text-white/90">
                    <span>📺</span>
                    YouTube Channels
                </label>

                <div className="space-y-2">
                    {channels.map((channel, index) => (
                        <div key={index} className="flex gap-2">
                            <input
                                type="text"
                                className="input-base flex-1"
                                placeholder="@channelname or channel URL"
                                value={channel}
                                onChange={(e) => updateChannel(index, e.target.value)}
                                required
                            />
                            <button
                                type="button"
                                onClick={() => removeChannel(index)}
                                disabled={channels.length === 1}
                                className="px-3 py-2 bg-white/5 border border-white/10 rounded-xl text-gray-400 
                         hover:text-red-400 hover:border-red-400/30 transition-colors
                         disabled:opacity-30 disabled:cursor-not-allowed"
                            >
                                ×
                            </button>
                        </div>
                    ))}
                </div>

                <button
                    type="button"
                    onClick={addChannel}
                    className="flex items-center gap-2 text-sm text-accent-primary hover:underline"
                >
                    <span>+</span> Add Another Channel
                </button>
                <span className="text-xs text-gray-500">
                    Enter YouTube channel names (e.g., @mkbhd) or full URLs
                </span>
            </div>

            {error && (
                <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-xl text-red-400 text-sm">
                    {error}
                </div>
            )}

            <Button type="submit" loading={status === 'loading'} className="w-full">
                Subscribe to Updates
            </Button>
        </form>
    );
}
