import { useState } from 'react';
import { Tabs, TabPanel } from './components/ui';
import { Header, Features } from './components/layout';
import { AnalysisForm } from './components/analysis';
import { SubscriptionForm } from './components/subscription';

const TABS = [
    { id: 'analyze', label: 'Analyze Video', icon: '🎬' },
    { id: 'subscribe', label: 'Subscribe to Channels', icon: '📺' },
];

function App() {
    const [activeTab, setActiveTab] = useState('analyze');

    return (
        <div className="min-h-screen relative overflow-hidden">
            {/* Background Effects */}
            <div className="fixed inset-0 pointer-events-none">
                <div className="gradient-orb orb-1" />
                <div className="gradient-orb orb-2" />
                <div className="gradient-orb orb-3" />
            </div>

            {/* Main Content */}
            <main className="relative z-10 max-w-4xl mx-auto px-4 pb-12">
                <Header />

                <section className="glass-card p-6 md:p-8">
                    <Tabs tabs={TABS} activeTab={activeTab} onTabChange={setActiveTab}>
                        <TabPanel id="analyze" activeTab={activeTab}>
                            <AnalysisForm />
                        </TabPanel>
                        <TabPanel id="subscribe" activeTab={activeTab}>
                            <SubscriptionForm />
                        </TabPanel>
                    </Tabs>
                </section>

                <Features />
            </main>

            {/* Footer */}
            <footer className="relative z-10 text-center py-6 text-gray-500 text-sm">
                Investment Streamer Analyzer © {new Date().getFullYear()} - Build: 2025-12-19_0109
            </footer>
        </div>
    );
}

export default App;
