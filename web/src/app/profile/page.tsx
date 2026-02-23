export const dynamic = 'force-dynamic';
import { fetchProfile } from '@/lib/api';

export default async function Profile() {
    const profile = await fetchProfile();

    if (!profile) {
        return (
            <div className="glass-card text-center p-12">
                <h2 className="text-2xl font-bold mb-2">No Profile Found</h2>
                <p className="text-gray-400">Run the CLI analyzer to build your digital avatar.</p>
            </div>
        );
    }

    return (
        <div className="space-y-8 animate-in fade-in duration-500">
            <header className="flex justify-between items-end">
                <div>
                    <h1 className="text-4xl font-extrabold tracking-tight mb-2">Author Profile</h1>
                    <p className="text-gray-400">Your AI-learned writing style and thematic digital twin.</p>
                </div>
                <div className="text-right glass px-4 py-2 rounded-xl">
                    <div className="text-xs text-gray-500 uppercase tracking-wider mb-1">Version {profile.version}</div>
                    <div className="font-mono text-primary-400">{profile.sample_count} Samples</div>
                </div>
            </header>

            <div className="glass-card">
                <h2 className="text-lg font-semibold text-white mb-3">AI Voice Description</h2>
                <p className="text-gray-300 leading-relaxed text-lg">{profile.voice_description}</p>
            </div>

            <div className="grid lg:grid-cols-2 gap-6">
                <div className="glass-card">
                    <h2 className="text-lg font-semibold text-white mb-4">Core Themes</h2>
                    <ul className="space-y-2">
                        {profile.themes.map((t: string, i: number) => (
                            <li key={i} className="flex items-start">
                                <span className="text-primary-500 mr-2">✦</span>
                                <span className="text-gray-300">{t}</span>
                            </li>
                        ))}
                    </ul>
                </div>

                <div className="glass-card">
                    <h2 className="text-lg font-semibold text-white mb-4">Top Interests</h2>
                    <div className="flex flex-wrap gap-2">
                        {profile.interests.map((intel: string, i: number) => (
                            <span key={i} className="bg-surface-800 text-gray-300 border border-white/5 px-3 py-1.5 rounded-lg text-sm">
                                {intel}
                            </span>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
}
