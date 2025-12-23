export function Header() {
    return (
        <header className="text-center py-12">
            <div className="flex items-center justify-center gap-3 mb-6">
                <span className="text-4xl">📊</span>
                <span className="text-2xl font-bold text-white">Investment Streamer Analyzer</span>
            </div>
            <h1 className="text-4xl md:text-5xl font-bold mb-4">
                Stay Ahead with{' '}
                <span className="gradient-text">AI-Powered</span>{' '}
                Video Analysis
            </h1>
            <p className="text-lg text-gray-400 max-w-2xl mx-auto">
                Subscribe to your favorite YouTube investment channels and receive intelligent
                analysis emails whenever new content is published.
            </p>
        </header>
    );
}
