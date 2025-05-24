from typing import List, Dict
from datetime import datetime, timedelta

def get_date(offset_days: int) -> str:
    return (datetime.now() - timedelta(days=offset_days)).strftime("%m/%d/%Y")


def generate_prompts(subject: str, focuses: List[str]) -> List[Dict]:
    prompts = []
    for focus in focuses:
        if focus == "news":
            prompts.append({
                "pillar": "news_recent",
                "prompt": f"What are the most important news updates about {subject} from the past 7 days? Include sources.",
                "after_date": get_date(7),
                "before_date": get_date(0),
                "context_size": "high"
            })
            prompts.append({
                "pillar": "news_long_term",
                "prompt": f"What were the major turning points or historical news events that shaped {subject}? Include sources.",
                "after_date": get_date(365 * 3),
                "before_date": get_date(30),
                "context_size": "high"
            })

        elif focus == "financial":
            prompts.append({
                "pillar": "financial",
                "prompt": f"Summarize the recent financial performance of {subject}. Include revenue, earnings, margins, and growth trends.",
                "context_size": "medium"
            })

        elif focus == "market":
            prompts.append({
                "pillar": "market",
                "prompt": f"What is the current market landscape for {subject}? Who are the main players and what's driving demand?",
                "context_size": "medium"
            })
            prompts.append({
                "pillar": "market_trend",
                "prompt": f"What long-term market trends are impacting {subject}? Focus on economic, policy, or tech shifts.",
                "context_size": "high"
            })

        elif focus == "adoption":
            prompts.append({
                "pillar": "adoption",
                "prompt": f"What is the current level of customer or industry adoption of {subject}? Are there any usage patterns or barriers?",
                "context_size": "medium"
            })

        elif focus == "competitor":
            prompts.append({
                "pillar": "competitor",
                "prompt": f"Who are the top competitors of {subject}? What moves have they made recently?",
                "context_size": "medium"
            })

        elif focus == "contextual":
            prompts.append({
                "pillar": "contextual",
                "prompt": f"Provide helpful background information or framing needed to understand the situation around {subject}.",
                "context_size": "low"
            })

    return prompts
