from typing import List, Dict, Any


def parse_sonar_responses(responses: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Organize Perplexity responses by pillar, including content and citations.
    
    Input: List of {pillar: str, content: str, citations: List}
    Output: Dict mapping each pillar to:
        {
            "content": full text,
            "citations": [merged list of all citations under this pillar]
        }
    """
    structured_output: Dict[str, Dict[str, Any]] = {}

    for item in responses:
        pillar = item.get("pillar", "unknown")
        content = item.get("content", "")
        citations = item.get("citations", [])

        if pillar not in structured_output:
            structured_output[pillar] = {
                "content": content,
                "citations": citations
            }
        else:
            structured_output[pillar]["content"] += f"\n\n{content}"
            structured_output[pillar]["citations"].extend(citations)

    return structured_output
