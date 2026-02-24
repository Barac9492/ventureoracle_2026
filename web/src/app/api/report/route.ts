import { NextRequest, NextResponse } from 'next/server';

export async function POST(req: NextRequest) {
    try {
        const { contentSummary } = await req.json();
        const apiKey = process.env.ANTHROPIC_API_KEY;

        if (!apiKey) {
            return NextResponse.json({ error: 'ANTHROPIC_API_KEY is not configured on the server.' }, { status: 500 });
        }

        const response = await fetch("https://api.anthropic.com/v1/messages", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "x-api-key": apiKey,
                "anthropic-version": "2023-06-01"
            },
            body: JSON.stringify({
                model: "claude-3-5-sonnet-20241022",
                max_tokens: 4000,
                system: "You are an LP report writer for TheVentures. CIO is Ethan Cho. Summarize the provided content into a professional quarterly report.",
                messages: [
                    {
                        role: "user",
                        content: `Generate LP quarterly brief. Content: ${contentSummary}`,
                    },
                ],
            }),
        });

        if (!response.ok) {
            const errorData = await response.json();
            const message = errorData.error?.message || 'AI Report generation failed';
            return NextResponse.json({ error: message }, { status: response.status });
        }

        const data = await response.json();
        return NextResponse.json(data);
    } catch (error) {
        console.error('Report generation error:', error);
        return NextResponse.json({ error: 'Failed to generate report' }, { status: 500 });
    }
}
