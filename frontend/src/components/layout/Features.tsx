export function Features() {
    const features = [
        {
            icon: '🤖',
            title: 'AI-Powered Analysis',
            description: 'Gemini AI extracts companies, stocks, and investment insights from video transcripts',
        },
        {
            icon: '⚡',
            title: 'Real-Time Notifications',
            description: 'Get notified as soon as new videos are published and transcripts become available',
        },
        {
            icon: '📧',
            title: 'Email Reports',
            description: 'Receive beautifully formatted reports with sentiment analysis and direct links',
        },
    ];

    return (
        <section className="grid md:grid-cols-3 gap-6 mt-12">
            {features.map((feature) => (
                <div
                    key={feature.title}
                    className="glass-card p-6 text-center hover:scale-[1.02] transition-transform"
                >
                    <div className="text-4xl mb-4">{feature.icon}</div>
                    <h3 className="text-lg font-semibold text-white mb-2">{feature.title}</h3>
                    <p className="text-sm text-gray-400">{feature.description}</p>
                </div>
            ))}
        </section>
    );
}
