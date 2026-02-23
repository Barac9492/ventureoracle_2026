"use client";

import Link from 'next/link';
import { usePathname } from 'next/navigation';

export default function Sidebar() {
    const pathname = usePathname();

    const navItems = [
        { name: 'Dashboard', path: '/' },
        { name: 'Discoveries', path: '/discoveries' },
        { name: 'Predictions', path: '/predictions' },
        { name: 'Profile', path: '/profile' },
    ];

    return (
        <div className="w-64 h-full glass border-r flex flex-col shrink-0">
            <div className="p-6">
                <h1 className="text-2xl font-bold text-gradient tracking-tight">VentureOracle</h1>
            </div>

            <nav className="flex-1 px-4 space-y-2 mt-4">
                {navItems.map((item) => {
                    const isActive = pathname === item.path;
                    return (
                        <Link
                            key={item.path}
                            href={item.path}
                            className={`block px-4 py-3 rounded-xl transition-all duration-200 font-medium ${isActive
                                    ? 'bg-primary-500/10 text-primary-400 shadow-[inset_0_1px_1px_rgba(255,255,255,0.1)]'
                                    : 'text-gray-400 hover:text-white hover:bg-white/5'
                                }`}
                        >
                            {item.name}
                        </Link>
                    );
                })}
            </nav>

            <div className="p-6 border-t border-white/5">
                <div className="text-xs text-gray-500 font-mono">
                    System Status: Online<br />
                    Engine: Claude-3.5
                </div>
            </div>
        </div>
    );
}
