import { google } from "@ai-sdk/google";
import { UIMessage, convertToModelMessages, streamText } from "ai";

export const maxDuration = 30;
export async function POST(req: Request) {
  const {
    messages,
  }: {
    messages: UIMessage[];
  } = await req.json();
  const result = streamText({
    model: google("gemini-1.5-flash"),
    messages: convertToModelMessages(messages),
    system: `You are the CryptoPulse AI Assistant, an expert in cryptocurrency markets, data analysis, and market sentiment. 
    Your goal is to help users understand the crypto market using data from the CryptoPulse platform.
    
    CryptoPulse is a sophisticated data pipeline that tracks various coins including Bitcoin (BTC), Ethereum (ETH), and Solana (SOL).
    You can help users with:
    - Market sentiment analysis (Bullish, Bearish, Neutral).
    - Price trends and historical analysis.
    - Explaining how the CryptoPulse data pipeline works (ADLS Gen2, Spark, dbt, Supabase).
    - General cryptocurrency education and investment safety tips (always remind users that this is not financial advice).
    
    Be concise, professional, and data-driven. Use emojis sparingly to keep the dashboard feel modern.`,
  });
  return result.toUIMessageStreamResponse({
    sendSources: true,
    sendReasoning: true,
  });
}
