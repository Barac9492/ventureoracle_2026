'use client';

import { useState, useEffect, useCallback } from "react";

interface Post {
    id: string;
    source: string;
    title: string;
    content: string;
    url?: string;
    publishedDate?: string | number;
    addedAt: string;
    theme: string;
    keyInsight: string;
}

interface ReportDraft {
    content: string;
    generatedAt: string;
    postCount: number;
    dateRange: string;
}

const THEMES = [
    "AI Infrastructure",
    "Korean Diaspora",
    "Korean VC Ecosystem",
    "Demographics & Aging",
    "Consumer Tech",
    "Founder Intelligence",
    "Regulatory & Policy",
    "Global Macro",
    "Other",
];

const SOURCES = ["Substack", "LinkedIn", "Other"];

// Storage keys
const POSTS_KEY = "contrarian-brief-posts";
const REPORT_KEY = "contrarian-brief-report";

export default function ContrarianBriefPage() {
    const [posts, setPosts] = useState<Post[]>([]);
    const [view, setView] = useState("dashboard"); // dashboard, add, library, report
    const [loading, setLoading] = useState(true);
    const [reportDraft, setReportDraft] = useState<ReportDraft | null>(null);
    const [generating, setGenerating] = useState(false);
    const [editingPost, setEditingPost] = useState<string | null>(null);

    // Load from storage
    useEffect(() => {
        function load() {
            try {
                const storedPosts = localStorage.getItem(POSTS_KEY);
                if (storedPosts) {
                    setPosts(JSON.parse(storedPosts));
                }
            } catch (e) {
                console.log("No existing posts data");
            }
            try {
                const storedReport = localStorage.getItem(REPORT_KEY);
                if (storedReport) {
                    setReportDraft(JSON.parse(storedReport));
                }
            } catch (e) {
                console.log("No existing report data");
            }
            setLoading(false);
        }
        load();
    }, []);

    // Save posts
    const savePosts = useCallback(async (newPosts: Post[]) => {
        setPosts(newPosts);
        try {
            localStorage.setItem(POSTS_KEY, JSON.stringify(newPosts));
        } catch (e) {
            console.error("Save failed:", e);
        }
    }, []);

    const addPost = async (post: Omit<Post, 'id' | 'addedAt'>) => {
        const newPost: Post = {
            ...post,
            id: Date.now().toString(),
            addedAt: new Date().toISOString(),
        };
        const updated = [newPost, ...posts];
        await savePosts(updated);
        setView("library");
    };

    const deletePost = async (id: string) => {
        const updated = posts.filter((p) => p.id !== id);
        await savePosts(updated);
    };

    const updatePost = async (id: string, updates: Partial<Post>) => {
        const updated = posts.map((p) => (p.id === id ? { ...p, ...updates } : p));
        await savePosts(updated);
        setEditingPost(null);
    };

    const handleImportMemory = async (importedPosts: any[]) => {
        if (!Array.isArray(importedPosts)) return;
        const newPosts: Post[] = importedPosts.map((p, idx) => ({
            ...p,
            id: (Date.now() + idx).toString(),
            addedAt: p.addedAt || new Date().toISOString(),
            theme: p.theme || "Other",
            keyInsight: p.keyInsight || ""
        }));
        const updated = [...newPosts, ...posts];
        await savePosts(updated);
        alert(`${newPosts.length} posts imported successfully!`);
    };

    const generateReport = async () => {
        if (posts.length === 0) return;
        setGenerating(true);

        const themeGroups: { [key: string]: Post[] } = {};
        posts.forEach((p) => {
            const t = p.theme || "Other";
            if (!themeGroups[t]) themeGroups[t] = [];
            themeGroups[t].push(p);
        });

        const contentSummary = Object.entries(themeGroups)
            .map(
                ([theme, items]) =>
                    `\n## ${theme} (${items.length} posts)\n${items
                        .map(
                            (i) =>
                                `- [${i.source}] ${i.title}: ${i.keyInsight || i.content?.substring(0, 200)}`
                        )
                        .join("\n")}`
            )
            .join("\n");

        const dateRange = getDateRange(posts);

        try {
            // NOTE: Original code had missing API key. Keeping structure for user.
            const response = await fetch("https://api.anthropic.com/v1/messages", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    model: "claude-sonnet-4-20250514",
                    max_tokens: 1000,
                    system: `You are an LP report writer for TheVentures. CIO is Ethan Cho.`,
                    messages: [
                        {
                            role: "user",
                            content: `Generate LP quarterly brief. Content: ${contentSummary}`,
                        },
                    ],
                }),
            });

            const data = await response.json();
            const text = data.content
                ?.map((c: any) => c.text || "")
                .filter(Boolean)
                .join("\n");

            const draft: ReportDraft = {
                content: text,
                generatedAt: new Date().toISOString(),
                postCount: posts.length,
                dateRange,
            };
            setReportDraft(draft);
            localStorage.setItem(REPORT_KEY, JSON.stringify(draft));
            setView("report");
        } catch (e) {
            console.error("Generation failed:", e);
            alert("Report generation failed. Please try again.");
        }
        setGenerating(false);
    };

    const classifyPost = async (title: string, content: string) => {
        try {
            const response = await fetch("https://api.anthropic.com/v1/messages", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    model: "claude-sonnet-4-20250514",
                    max_tokens: 1000,
                    messages: [
                        {
                            role: "user",
                            content: `Classify content: ${title} ${content.substring(0, 500)}`,
                        },
                    ],
                }),
            });
            const data = await response.json();
            const text = data.content?.[0]?.text || "";
            const clean = text.replace(/```json|```/g, "").trim();
            return JSON.parse(clean);
        } catch (e) {
            return { theme: "Other", keyInsight: "", tags: [] };
        }
    };

    function getDateRange(items: Post[]) {
        if (items.length === 0) return "N/A";
        const dates = items
            .map((p) => p.publishedDate || p.addedAt)
            .filter(Boolean)
            .sort();
        if (dates.length === 0) return "N/A";
        const fmt = (d: any) =>
            new Date(d).toLocaleDateString("en-US", {
                month: "short",
                year: "numeric",
            });
        return `${fmt(dates[0])} – ${fmt(dates[dates.length - 1])}`;
    }

    function getThemeStats() {
        const stats: { [key: string]: number } = {};
        posts.forEach((p) => {
            const t = p.theme || "Other";
            stats[t] = (stats[t] || 0) + 1;
        });
        return Object.entries(stats).sort((a, b) => b[1] - a[1]);
    }

    if (loading) {
        return (
            <div style={styles.loadingScreen}>
                <div style={styles.loadingText}>Loading...</div>
            </div>
        );
    }

    return (
        <div style={styles.container}>
            <Header view={view} setView={setView} postCount={posts.length} />

            {view === "dashboard" && (
                <Dashboard
                    posts={posts}
                    themeStats={getThemeStats()}
                    dateRange={getDateRange(posts)}
                    onGenerate={generateReport}
                    onImport={handleImportMemory}
                    generating={generating}
                    setView={setView}
                    reportDraft={reportDraft}
                />
            )}

            {view === "add" && (
                <AddPost
                    onAdd={addPost}
                    onClassify={classifyPost}
                    setView={setView}
                />
            )}

            {view === "library" && (
                <Library
                    posts={posts}
                    onDelete={deletePost}
                    onUpdate={updatePost}
                    editingPost={editingPost}
                    setEditingPost={setEditingPost}
                />
            )}

            {view === "report" && (
                <Report
                    draft={reportDraft}
                    onRegenerate={generateReport}
                    generating={generating}
                />
            )}
        </div>
    );
}

// Components
function Header({ view, setView, postCount }: any) {
    return (
        <div style={styles.header}>
            <div style={styles.headerLeft}>
                <div style={styles.logo}>CB</div>
                <div>
                    <div style={styles.headerTitle}>Contrarian Brief</div>
                    <div style={styles.headerSub}>
                        {postCount} posts accumulated
                    </div>
                </div>
            </div>
            <nav style={styles.nav}>
                {[
                    ["dashboard", "Dashboard"],
                    ["add", "+ Add"],
                    ["library", "Library"],
                    ["report", "Report"],
                ].map(([key, label]) => (
                    <button
                        key={key}
                        onClick={() => setView(key)}
                        style={{
                            ...styles.navBtn,
                            ...(view === key ? styles.navBtnActive : {}),
                        }}
                    >
                        {label}
                    </button>
                ))}
            </nav>
        </div>
    );
}

function Dashboard({
    posts,
    themeStats,
    dateRange,
    onGenerate,
    onImport,
    generating,
    setView,
    reportDraft,
}: any) {
    const recentPosts = posts.slice(0, 5);

    const onFileChange = (e: any) => {
        const file = e.target.files[0];
        if (!file) return;
        const reader = new FileReader();
        reader.onload = (event) => {
            try {
                const json = JSON.parse(event?.target?.result as string);
                onImport(json);
            } catch (err) {
                alert("File parsing failed.");
            }
        };
        reader.readAsText(file);
    };

    return (
        <div style={styles.main}>
            <div style={styles.statsRow}>
                <StatCard label="Total Posts" value={posts.length} />
                <StatCard label="Themes" value={themeStats.length} />
                <StatCard label="Range" value={dateRange} small />
                <StatCard
                    label="Last Report"
                    value={
                        reportDraft
                            ? new Date(reportDraft.generatedAt).toLocaleDateString()
                            : "None"
                    }
                    small
                />
            </div>

            <div style={styles.twoCol}>
                <div style={styles.col}>
                    <div style={styles.sectionTitle}>Themes</div>
                    <div style={styles.card}>
                        {themeStats.length === 0 ? (
                            <div style={styles.emptyText}>No posts yet.</div>
                        ) : (
                            themeStats.map(([theme, count]: any) => (
                                <div key={theme} style={styles.themeBar}>
                                    <div style={styles.themeLabel}>{theme}</div>
                                    <div style={styles.barContainer}>
                                        <div
                                            style={{
                                                ...styles.bar,
                                                width: `${(count / posts.length) * 100}%`,
                                            }}
                                        />
                                    </div>
                                    <div style={styles.themeCount}>{count}</div>
                                </div>
                            ))
                        )}
                    </div>
                </div>

                <div style={styles.col}>
                    <div style={styles.sectionTitle}>Recent</div>
                    <div style={styles.card}>
                        {recentPosts.length === 0 ? (
                            <button onClick={() => setView("add")} style={styles.primaryBtn}>
                                + Add First Post
                            </button>
                        ) : (
                            recentPosts.map((p: any) => (
                                <div key={p.id} style={styles.recentItem}>
                                    <div style={styles.recentMeta}>
                                        <span style={styles.sourceTag}>{p.source}</span>
                                        <span style={styles.themeMini}>{p.theme}</span>
                                    </div>
                                    <div style={styles.recentTitle}>{p.title}</div>
                                </div>
                            ))
                        )}
                    </div>
                </div>
            </div>

            <div style={styles.generateSection}>
                <button
                    onClick={onGenerate}
                    disabled={generating}
                    style={styles.generateBtn}
                >
                    {generating ? "Generating..." : "Generate LP Report Draft"}
                </button>
            </div>

            <div style={{ ...styles.generateSection, paddingTop: 0 }}>
                <label style={styles.secondaryBtn}>
                    Import Memory Dump
                    <input
                        type="file"
                        accept=".json"
                        onChange={onFileChange}
                        style={{ display: "none" }}
                    />
                </label>
            </div>
        </div>
    );
}

function StatCard({ label, value, small }: any) {
    return (
        <div style={styles.statCard}>
            <div style={{ ...styles.statValue, fontSize: small ? 16 : 24 }}>
                {value}
            </div>
            <div style={styles.statLabel}>{label}</div>
        </div>
    );
}

function AddPost({ onAdd, onClassify, setView }: any) {
    const [source, setSource] = useState("Substack");
    const [title, setTitle] = useState("");
    const [content, setContent] = useState("");
    const [theme, setTheme] = useState("");
    const [keyInsight, setKeyInsight] = useState("");
    const [classifying, setClassifying] = useState(false);

    const handleClassify = async () => {
        setClassifying(true);
        const result = await onClassify(title, content);
        if (result.theme) setTheme(result.theme);
        if (result.keyInsight) setKeyInsight(result.keyInsight);
        setClassifying(false);
    };

    return (
        <div style={styles.main}>
            <div style={styles.sectionTitle}>Add Content</div>
            <div style={styles.addCard}>
                <div style={styles.fieldGroup}>
                    <label style={styles.label}>Source</label>
                    <div style={styles.sourceToggle}>
                        {SOURCES.map((s) => (
                            <button
                                key={s}
                                onClick={() => setSource(s)}
                                style={{
                                    ...styles.toggleBtn,
                                    ...(source === s ? styles.toggleBtnActive : {}),
                                }}
                            >
                                {s}
                            </button>
                        ))}
                    </div>
                </div>
                <div style={styles.fieldGroup}>
                    <label style={styles.label}>Title</label>
                    <input
                        value={title}
                        onChange={(e) => setTitle(e.target.value)}
                        style={styles.input}
                    />
                </div>
                <div style={styles.fieldGroup}>
                    <label style={styles.label}>Content</label>
                    <textarea
                        value={content}
                        onChange={(e) => setContent(e.target.value)}
                        style={styles.textarea}
                        rows={6}
                    />
                </div>
                <button onClick={handleClassify} style={styles.classifyBtn}>
                    {classifying ? "Classifying..." : "Auto-Classify"}
                </button>
                <div style={styles.fieldGroup}>
                    <label style={styles.label}>Theme</label>
                    <select value={theme} onChange={(e) => setTheme(e.target.value)} style={styles.select}>
                        <option value="">Select theme...</option>
                        {THEMES.map((t) => <option key={t} value={t}>{t}</option>)}
                    </select>
                </div>
                <div style={styles.fieldGroup}>
                    <label style={styles.label}>Key Insight</label>
                    <input value={keyInsight} onChange={(e) => setKeyInsight(e.target.value)} style={styles.input} />
                </div>
                <div style={styles.btnRow}>
                    <button onClick={() => setView("dashboard")} style={styles.cancelBtn}>Cancel</button>
                    <button onClick={() => onAdd({ source, title, content, theme, keyInsight })} style={styles.primaryBtn}>Save</button>
                </div>
            </div>
        </div>
    );
}

function Library({ posts, onDelete, onUpdate, editingPost, setEditingPost }: any) {
    return (
        <div style={styles.main}>
            <div style={styles.sectionTitle}>Library</div>
            <div style={styles.postList}>
                {posts.map((post: any) => (
                    <div key={post.id} style={styles.postCard}>
                        <div style={styles.postHeader}>
                            <span style={styles.sourceTag}>{post.source}</span>
                            <button onClick={() => onDelete(post.id)} style={styles.smallBtn}>Delete</button>
                        </div>
                        <div style={styles.postTitle}>{post.title}</div>
                        <div style={styles.postInsight}>{post.keyInsight}</div>
                    </div>
                ))}
            </div>
        </div>
    );
}

function Report({ draft, onRegenerate, generating }: any) {
    return (
        <div style={styles.main}>
            <div style={styles.sectionTitle}>Report Draft</div>
            <div style={styles.card}>
                <pre style={styles.reportContent}>{draft?.content}</pre>
                <button onClick={onRegenerate} style={styles.primaryBtn}>{generating ? "Regenerating..." : "Regenerate"}</button>
            </div>
        </div>
    );
}

// Styles
const styles: { [key: string]: React.CSSProperties } = {
    container: { background: "#0a0a0a", minHeight: "100vh", color: "#e8e8e8", fontFamily: "sans-serif" },
    loadingScreen: { display: "flex", alignItems: "center", justifyContent: "center", height: "100vh" },
    loadingText: { color: "#666" },
    header: { display: "flex", justifyContent: "space-between", padding: "16px 24px", borderBottom: "1px solid #1a1a1a" },
    headerLeft: { display: "flex", alignItems: "center", gap: 12 },
    logo: { background: "#c0945c", padding: "6px 8px", borderRadius: 4, color: "#000", fontWeight: "bold" },
    headerTitle: { fontSize: 16, fontWeight: "bold" },
    headerSub: { fontSize: 12, color: "#666" },
    nav: { display: "flex", gap: 8 },
    navBtn: { background: "transparent", border: "none", color: "#888", cursor: "pointer" },
    navBtnActive: { color: "#c0945c" },
    main: { padding: 24, maxWidth: 800, margin: "0 auto" },
    statsRow: { display: "flex", gap: 12, marginBottom: 24 },
    statCard: { flex: 1, background: "#111", padding: 16, borderRadius: 8, border: "1px solid #1a1a1a" },
    statValue: { color: "#c0945c", fontWeight: "bold" },
    statLabel: { fontSize: 10, color: "#666", textTransform: "uppercase" },
    twoCol: { display: "flex", gap: 16 },
    col: { flex: 1 },
    sectionTitle: { fontSize: 12, color: "#666", marginBottom: 12, textTransform: "uppercase" },
    card: { background: "#111", padding: 16, borderRadius: 8, border: "1px solid #1a1a1a" },
    emptyText: { color: "#444", textAlign: "center" },
    themeBar: { marginBottom: 8 },
    themeLabel: { fontSize: 11, color: "#aaa" },
    barContainer: { height: 4, background: "#222", borderRadius: 2, overflow: "hidden" },
    bar: { height: "100%", background: "#c0945c" },
    themeCount: { fontSize: 10, color: "#666", textAlign: "right" },
    recentItem: { padding: "8px 0", borderBottom: "1px solid #1a1a1a" },
    recentMeta: { display: "flex", gap: 4, marginBottom: 4 },
    sourceTag: { fontSize: 9, background: "#1a1a1a", color: "#c0945c", padding: "2px 4px", borderRadius: 2 },
    themeMini: { fontSize: 9, color: "#666" },
    recentTitle: { fontSize: 12 },
    generateSection: { textAlign: "center", marginTop: 24 },
    generateBtn: { background: "#c0945c", color: "#000", padding: "12px 24px", borderRadius: 6, fontWeight: "bold", border: "none", cursor: "pointer" },
    secondaryBtn: { background: "#1a1a1a", color: "#aaa", padding: "8px 16px", borderRadius: 6, border: "1px solid #2a2a2a", cursor: "pointer" },
    addCard: { background: "#111", padding: 24, borderRadius: 8, border: "1px solid #1a1a1a" },
    fieldGroup: { marginBottom: 16 },
    label: { fontSize: 10, color: "#666", display: "block", marginBottom: 4 },
    sourceToggle: { display: "flex", gap: 4 },
    toggleBtn: { padding: "6px 12px", background: "#1a1a1a", border: "1px solid #2a2a2a", color: "#666", borderRadius: 4, cursor: "pointer" },
    toggleBtnActive: { background: "#c0945c", color: "#000" },
    input: { width: "100%", padding: 10, background: "#0a0a0a", border: "1px solid #2a2a2a", color: "#fff", borderRadius: 4 },
    textarea: { width: "100%", padding: 10, background: "#0a0a0a", border: "1px solid #2a2a2a", color: "#fff", borderRadius: 4 },
    classifyBtn: { background: "transparent", color: "#c0945c", border: "1px solid #c0945c", padding: "6px 12px", borderRadius: 4, marginBottom: 16, cursor: "pointer" },
    select: { width: "100%", padding: 10, background: "#0a0a0a", border: "1px solid #2a2a2a", color: "#fff", borderRadius: 4 },
    btnRow: { display: "flex", justifyContent: "flex-end", gap: 8 },
    primaryBtn: { background: "#c0945c", color: "#000", padding: "8px 16px", borderRadius: 4, fontWeight: "bold", border: "none", cursor: "pointer" },
    cancelBtn: { background: "transparent", color: "#666", border: "1px solid #222", padding: "8px 16px", borderRadius: 4, cursor: "pointer" },
    postList: { display: "flex", flexDirection: "column", gap: 8 },
    postCard: { background: "#111", padding: 16, borderRadius: 8, border: "1px solid #1a1a1a" },
    postHeader: { display: "flex", justifyContent: "space-between", marginBottom: 8 },
    smallBtn: { fontSize: 10, color: "#666", background: "transparent", border: "none", cursor: "pointer" },
    postTitle: { fontSize: 14, fontWeight: "bold" },
    postInsight: { fontSize: 12, color: "#c0945c", fontStyle: "italic" },
    reportContent: { fontSize: 13, color: "#aaa", whiteSpace: "pre-wrap" }
};
