"""
Brief rendering utilities.
"""

from typing import Dict, Any

def brief_to_markdown_full(brief_dict: Dict[str, Any]) -> str:
    """Convert a brief dictionary to full markdown format."""
    if not brief_dict:
        return "# Empty Brief\n\nNo content provided."
    
    markdown = []
    
    # Title
    if "title" in brief_dict:
        markdown.append(f"# {brief_dict['title']}")
    
    # Meta description
    if "meta_description" in brief_dict:
        markdown.append(f"**Meta Description:** {brief_dict['meta_description']}")
    
    # Content
    if "content" in brief_dict:
        markdown.append("\n## Content\n")
        markdown.append(brief_dict["content"])
    
    # Outline
    if "outline" in brief_dict:
        markdown.append("\n## Outline\n")
        if isinstance(brief_dict["outline"], list):
            for item in brief_dict["outline"]:
                markdown.append(f"- {item}")
        else:
            markdown.append(str(brief_dict["outline"]))
    
    # Keywords
    if "keywords" in brief_dict:
        markdown.append("\n## Keywords\n")
        if isinstance(brief_dict["keywords"], list):
            markdown.append(", ".join(brief_dict["keywords"]))
        else:
            markdown.append(str(brief_dict["keywords"]))
    
    return "\n\n".join(markdown)