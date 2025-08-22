"""
Export functionality for AI Keyword Tool sessions.
Supports Markdown export with optional PDF conversion.
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Any, Optional


def export_to_markdown(session_id: str, session_data: Dict[str, Any]) -> str:
    """
    Export a complete session to Markdown format.
    
    Args:
        session_id: Unique session identifier
        session_data: Dictionary containing session, brief, suggestions, and serp data
    
    Returns:
        Absolute file path of the exported Markdown file
    """
    # Extract data components
    session = session_data.get("session", {})
    brief = session_data.get("brief", {})
    suggestions = session_data.get("suggestions", [])
    serp = session_data.get("serp", {})
    
    # Create filename with timestamp for uniqueness
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_topic = "".join(c for c in session.get("topic", "session") if c.isalnum() or c in (' ', '-', '_')).strip()
    safe_topic = safe_topic.replace(' ', '_')[:50]  # Limit length
    filename = f"{safe_topic}_{timestamp}.md"
    
    # Build Markdown content
    markdown_content = _build_markdown_content(session, brief, suggestions, serp)
    
    # Write to file
    filepath = os.path.abspath(filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(markdown_content)
    
    return filepath


def _build_markdown_content(session: Dict, brief: Dict, suggestions: List[Dict], serp: Dict) -> str:
    """Build the complete Markdown content for export."""
    
    # Header section
    topic = session.get("topic", "Unknown Topic")
    created_at = session.get("created_at", "Unknown Date")
    
    # Try to format the date nicely
    try:
        if created_at and created_at != "Unknown Date":
            date_obj = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            formatted_date = date_obj.strftime("%B %d, %Y at %I:%M %p")
        else:
            formatted_date = created_at
    except:
        formatted_date = created_at
    
    content = f"""# 🎯 Content Strategy: {topic}

**Generated:** {formatted_date}  
**Session ID:** {session.get('id', 'N/A')}

---

"""

    # Brief section
    if brief and brief.get("content"):
        content += f"""## 🧠 AI Content Brief

{brief['content']}

---

"""

    # Suggestions section
    if suggestions:
        content += "## 💡 AI Strategy Suggestions\n\n"
        
        # Group suggestions by variant
        suggestions_by_variant = {}
        for suggestion in suggestions:
            variant = suggestion.get('variant', 'general')
            if variant not in suggestions_by_variant:
                suggestions_by_variant[variant] = []
            suggestions_by_variant[variant].append(suggestion)
        
        # Render each variant section
        variant_titles = {
            'quick_wins': '🚀 Quick Wins',
            'content_ideas': '📝 Content Ideas', 
            'technical_seo': '🔧 Technical SEO',
            'general': '💭 General Suggestions'
        }
        
        for variant, variant_suggestions in suggestions_by_variant.items():
            title = variant_titles.get(variant, f"📋 {variant.title()}")
            content += f"### {title}\n\n"
            
            for suggestion in variant_suggestions:
                suggestion_content = suggestion.get('content', '').strip()
                if suggestion_content:
                    # Add proper indentation for multi-line content
                    lines = suggestion_content.split('\n')
                    formatted_content = '\n'.join(lines)
                    content += f"{formatted_content}\n\n"
        
        content += "---\n\n"

    # SERP analysis section
    if serp and serp.get("data"):
        content += "## 🔍 SERP Analysis\n\n"
        
        try:
            serp_data = json.loads(serp["data"])
            if isinstance(serp_data, list) and len(serp_data) > 0:
                content += f"**Total Results Analyzed:** {len(serp_data)}\n\n"
                content += "### Top Competitors\n\n"
                
                for i, result in enumerate(serp_data[:5], 1):
                    title = result.get('title', 'No Title')
                    url = result.get('url', 'No URL')
                    snippet = result.get('snippet', 'No snippet available')
                    
                    content += f"**{i}. {title}**\n"
                    content += f"- URL: {url}\n"
                    content += f"- Snippet: {snippet[:200]}{'...' if len(snippet) > 200 else ''}\n\n"
            else:
                content += "No SERP data available.\n\n"
        except json.JSONDecodeError:
            content += "SERP data format error.\n\n"
        except Exception as e:
            content += f"Error processing SERP data: {str(e)}\n\n"
        
        content += "---\n\n"

    # Footer
    content += f"""## 📋 Export Information

**Export Date:** {datetime.now().strftime("%B %d, %Y at %I:%M %p")}  
**Generated by:** AI Keyword Strategy Generator  
**Session ID:** {session.get('id', 'N/A')}

---

*This content brief was generated using AI technology. Please review and customize as needed for your specific requirements.*
"""

    return content


def get_export_filename_preview(topic: str) -> str:
    """
    Get a preview of what the export filename would be.
    
    Args:
        topic: Session topic
    
    Returns:
        Preview filename (without timestamp)
    """
    safe_topic = "".join(c for c in topic if c.isalnum() or c in (' ', '-', '_')).strip()
    safe_topic = safe_topic.replace(' ', '_')[:50]
    return f"{safe_topic}_[timestamp].md"
