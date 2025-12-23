// Validation patterns
const YOUTUBE_URL_PATTERN = /^https?:\/\/(www\.)?(youtube\.com|youtu\.be)\//;
const YOUTUBE_VIDEO_ID_PATTERN = /^[a-zA-Z0-9_-]{11}$/;
const YOUTUBE_CHANNEL_PATTERN = /^@?[a-zA-Z0-9_.-]{1,100}$/;
const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const MAX_URL_LENGTH = 300;

export function isValidVideoUrl(url: string): boolean {
    if (!url || url.length > MAX_URL_LENGTH) return false;
    const trimmed = url.trim();

    // Direct video ID (11 characters)
    if (trimmed.length === 11 && YOUTUBE_VIDEO_ID_PATTERN.test(trimmed)) return true;

    // Full URL
    if (YOUTUBE_URL_PATTERN.test(trimmed)) return true;

    return false;
}

export function isValidChannelUrl(url: string): boolean {
    if (!url || url.length > MAX_URL_LENGTH) return false;
    const trimmed = url.trim();

    // @username format
    if (trimmed.startsWith('@') && YOUTUBE_CHANNEL_PATTERN.test(trimmed)) return true;

    // Full URL
    if (YOUTUBE_URL_PATTERN.test(trimmed)) return true;

    // Plain username
    if (YOUTUBE_CHANNEL_PATTERN.test(trimmed)) return true;

    return false;
}

export function isValidEmail(email: string): boolean {
    if (!email) return true; // Optional
    return email.length <= 254 && EMAIL_PATTERN.test(email);
}

export function timestampToSeconds(timestamp: string): number {
    if (!timestamp) return 0;
    const clean = timestamp.replace(/[\[\]]/g, '');
    const parts = clean.split(':');
    if (parts.length === 2) {
        return parseInt(parts[0]) * 60 + parseInt(parts[1]);
    }
    return 0;
}
