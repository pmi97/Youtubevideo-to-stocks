const API_BASE = import.meta.env.VITE_API_URL || '';

export async function analyzeVideo(data: {
    video_url: string;
    email?: string;
    language: string;
}) {
    const response = await fetch(`${API_BASE}/analyze-video`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || 'Failed to analyze video. Please try again.');
    }

    return response.json();
}

export async function subscribe(data: {
    email: string;
    language: string;
    channels: { url: string }[];
}) {
    const response = await fetch(`${API_BASE}/subscribe`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || 'Failed to subscribe. Please try again.');
    }

    return response.json();
}
