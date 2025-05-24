from typing import Dict


def generate_360_summary(structured_data: Dict[str, str]) -> str:
    """
    Summarize all pillar outputs into a cohesive overview.
    """
    summary_sections = []

    if "news" in structured_data:
        summary_sections.append("**Recent News**\n" + structured_data["news"])

    if "sentiment" in structured_data:
        summary_sections.append("**Market/Public Sentiment**\n" + structured_data["sentiment"])

    if "financial" in structured_data:
        summary_sections.append("**Financial Overview**\n" + structured_data["financial"])

    if "market" in structured_data:
        summary_sections.append("**Market Landscape**\n" + structured_data["market"])

    if "competitor" in structured_data:
        summary_sections.append("**Competitive Activity**\n" + structured_data["competitor"])

    if "adoption" in structured_data:
        summary_sections.append("**Adoption and Customer Trends**\n" + structured_data["adoption"])
        
    if "contextual" in structured_data:
        summary_sections.append("**Contextual Analysis**\n" + structured_data["contextual"])

    return "\n\n".join(summary_sections).strip()