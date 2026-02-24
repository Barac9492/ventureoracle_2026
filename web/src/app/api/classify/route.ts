import { NextRequest, NextResponse } from 'next/server';

export async function POST(req: NextRequest) {
    try {
        const { title, content } = await req.json();
        const apiKey = process.env.ANTHROPIC_API_KEY;

        if (!apiKey) {
            return NextResponse.json({ error: 'ANTHROPIC_API_KEY is missing' }, { status: 500 });
        }

        const response = await fetch("https://api.anthropic.com/v1/messages", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "x-api-key": apiKey,
                "anthropic-version": "2023-06-01"
            },
            body: JSON.stringify({
                model: "claude-3-haiku-20240307",
                max_tokens: 1000,
                messages: [
                    {
                        role: "user",
                        content: `Classify the following content into one of these themes: AI Infrastructure, Korean Diaspora, Korean VC Ecosystem, Demographics & Aging, Consumer Tech, Founder Intelligence, Regulatory & Policy, Global Macro, Other. 
            Also extract a one-sentence key insight.
            Return ONLY a JSON object with "theme" and "keyInsight" keys.
            
            Title: ${title}
            Content: ${content.substring(0, 1000)}`,
                    },
                ],
            }),
        });

        if (!response.ok) {
            const errorData = await response.json();
            return NextResponse.json({ error: errorData.error?.message || 'AI Classification failed' }, { status: response.status });
        }

        const data = await response.json();
        return NextResponse.json(data);
    } catch (error) {
        console.error('Classification error:', error);
        return NextResponse.json({ error: 'Failed to classify' }, { status: 500 });
    }
}
