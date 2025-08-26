"""
Multi-Entry Step Renderers for AI Keyword Tool
Flexible entry points based on user needs
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any, Optional

# Import core services
try:
    from ..core.state_manager import state_manager
    from ..core.services import KeywordService, generate_brief_with_variant, fetch_serp_snapshot
    from ..utils.scoring import add_scores, analyze_keyword
    from ..utils.db_utils import safe_save_session, safe_save_brief
except ImportError:
    # Fallback for missing imports
    class SimpleStateManager:
        def go_to_step(self, step: int):
            st.session_state.ux_step = step
    state_manager = SimpleStateManager()


def render_current_step():
    """Main entry point - route users based on their needs"""
    
    # First-time visitors choose their path
    if not st.session_state.get("entry_point"):
        render_entry_selection()
        return
    
    # Add flow switcher to sidebar
    render_flow_switcher()
    
    # Route to appropriate flow
    entry_point = st.session_state.get("entry_point")
    step = st.session_state.get("ux_step", 1)
    
    if entry_point == "keyword_discovery":
        render_keyword_discovery_flow(step)
    elif entry_point == "keyword_to_strategy":
        render_keyword_to_strategy_flow(step)
    elif entry_point == "custom_brief":
        render_custom_brief_flow(step)
    elif entry_point == "ideas_only":
        render_ideas_only_flow(step)


def render_entry_selection():
    """Let users choose their starting point"""
    st.markdown("""
    <div style="text-align: center; padding: 2rem 0;">
    <h2>🎯 What brings you here today?</h2>
    <p style="color: #666; font-size: 1.1rem;">Choose your starting point to get the most relevant experience</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Entry point selection
    entry_choice = st.radio(
        "**Choose your path:**",
        [
            "🔍 I need help finding the right keywords",
            "🎯 I have a keyword and want a content strategy", 
            "📝 I want to create a content brief from scratch",
            "💡 I just want content ideas and strategy"
        ],
        help="Select the option that best matches what you want to accomplish"
    )
    
    # Show preview of what each path includes
    if entry_choice == "🔍 I need help finding the right keywords":
        st.info("**Path:** Business Context → Keyword Generation → Complete Strategy")
        if st.button("Start Keyword Discovery", type="primary"):
            st.session_state.entry_point = "keyword_discovery"
            st.session_state.ux_step = 1
            st.rerun()
            
    elif entry_choice == "🎯 I have a keyword and want a content strategy":
        st.info("**Path:** Keyword Entry → Analysis → Complete Strategy")
        if st.button("Create Strategy from Keyword", type="primary"):
            st.session_state.entry_point = "keyword_to_strategy"
            st.session_state.ux_step = 1
            st.rerun()
            
    elif entry_choice == "📝 I want to create a content brief from scratch":
        st.info("**Path:** Brief Creator → Market Analysis → Strategy")
        if st.button("Create Custom Brief", type="primary"):
            st.session_state.entry_point = "custom_brief"
            st.session_state.ux_step = 1
            st.rerun()
            
    elif entry_choice == "💡 I just want content ideas and strategy":
        st.info("**Path:** Quick Context → Content Ideas → Strategy")
        if st.button("Generate Content Ideas", type="primary"):
            st.session_state.entry_point = "ideas_only"
            st.session_state.ux_step = 1
            st.rerun()


def render_flow_switcher():
    """Allow users to switch between flows"""
    with st.sidebar:
        st.markdown("### Quick Actions")
        
        current_entry = st.session_state.get("entry_point", "None")
        st.caption(f"Current path: {current_entry.replace('_', ' ').title()}")
        
        if st.button("🔄 Switch Approach"):
            # Clear current flow and return to entry selection
            st.session_state.entry_point = None
            st.session_state.ux_step = 1
            st.rerun()
        
        if st.button("🏠 Start Over"):
            # Complete reset
            for key in list(st.session_state.keys()):
                if key not in ["dev_mode"]:
                    del st.session_state[key]
            st.rerun()


# Flow 1: Keyword Discovery Flow
def render_keyword_discovery_flow(step):
    """Complete keyword discovery to strategy flow"""
    st.progress(step / 3)
    st.caption(f"Step {step} of 3 - Keyword Discovery Path")
    
    if step == 1:
        render_business_context()
    elif step == 2:
        render_ai_keyword_generation()
    elif step == 3:
        render_complete_strategy()


def render_business_context():
    """Step 1: Business context collection"""
    st.markdown("### 🏢 Tell us about your business")
    st.info("💡 This helps us generate more relevant and targeted keywords for you")
    
    business_desc = st.text_area(
        "Describe your business, product, or service:",
        value=st.session_state.get("seed_input", ""),
        height=120,
        placeholder="e.g., We provide digital marketing services for small businesses, focusing on SEO, social media management, and content creation."
    )
    
    # Optional additional context
    col1, col2 = st.columns(2)
    with col1:
        industry = st.text_input(
            "Industry (optional):",
            value=st.session_state.get("industry_input", ""),
            placeholder="e.g., Digital Marketing"
        )
    with col2:
        target_audience = st.text_input(
            "Target Audience (optional):",
            value=st.session_state.get("audience_input", ""),
            placeholder="e.g., Small business owners"
        )
    
    # Save to session state
    st.session_state.seed_input = business_desc
    st.session_state.industry_input = industry
    st.session_state.audience_input = target_audience
    
    if business_desc.strip():
        if st.button("🔍 Generate Keywords", type="primary"):
            state_manager.go_to_step(2)
    else:
        st.warning("Please describe your business to continue")


def render_ai_keyword_generation():
    """Step 2: AI keyword generation and selection"""
    st.markdown("### 🔑 Choose Your Target Keyword")
    
    # Generate keywords if not already done
    if not st.session_state.get("keywords_data"):
        with st.spinner("Generating keywords..."):
            service = KeywordService()
            keywords_data = service.generate_keywords(
                business_desc=st.session_state.seed_input,
                industry=st.session_state.get("industry_input", ""),
                audience=st.session_state.get("audience_input", "")
            )
            st.session_state.keywords_data = keywords_data
    
    # Display keywords
    keywords_data = st.session_state.keywords_data
    
    # Convert to dataframe
    all_keywords = []
    for category, kws in keywords_data.items():
        for kw in kws:
            if isinstance(kw, dict):
                row = {
                    "keyword": kw["keyword"],
                    "category": category,
                    "volume": kw.get("volume", 0),
                    "difficulty": kw.get("difficulty", 50),
                    "quick_win_score": kw.get("quick_win_score", 50)
                }
            else:
                row = {"keyword": kw, "category": category}
            all_keywords.append(row)
    
    if all_keywords:
        df = pd.DataFrame(all_keywords)
        df = add_scores(df)  # Add realistic scores
        
        # Show top keywords
        st.markdown("#### 🎯 AI-Generated Keywords")
        
        # Color coding for scores
        def highlight_scores(row):
            score = row['quick_win_score']
            if score >= 80:
                return ['background-color: #dcfce7'] * len(row)
            elif score >= 60:
                return ['background-color: #fef3c7'] * len(row)
            else:
                return ['background-color: #fee2e2'] * len(row)
        
        styled_df = df.style.apply(highlight_scores, axis=1)
        st.dataframe(styled_df, use_container_width=True)
        
        # Selection
        keyword_options = df["keyword"].tolist()
        selected = st.selectbox("Select a keyword:", [""] + keyword_options)
        
        if selected:
            kw_row = df[df["keyword"] == selected].iloc[0]
            st.info(f"**{selected}** • Score: {kw_row['quick_win_score']} • Volume: {kw_row.get('volume', 'N/A')} • Difficulty: {kw_row['difficulty']}")
            
            if st.button("📝 Create Strategy", type="primary"):
                st.session_state.selected_keyword = selected
                state_manager.go_to_step(3)
    
    # Navigation
    if st.button("← Back to Business Context"):
        state_manager.go_to_step(1)


# Flow 2: Keyword to Strategy Flow  
def render_keyword_to_strategy_flow(step):
    """Direct keyword to strategy flow"""
    st.progress(step / 2)
    st.caption(f"Step {step} of 2 - Keyword to Strategy Path")
    
    if step == 1:
        render_direct_keyword_entry()
    elif step == 2:
        render_complete_strategy()


def render_direct_keyword_entry():
    """Direct keyword entry with analysis"""
    st.markdown("### 🎯 What's your target keyword?")
    
    keyword = st.text_input(
        "Enter your keyword:",
        value=st.session_state.get("selected_keyword", ""),
        placeholder="e.g., best project management software"
    )
    
    if keyword:
        # Real-time keyword analysis
        try:
            analysis = analyze_keyword(keyword)
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Volume", analysis.get('search_volume', 'N/A'))
            with col2:
                st.metric("Difficulty", analysis.get('difficulty', 'N/A'))
            with col3:
                st.metric("Quick-Win Score", analysis.get('quick_win_score', 'N/A'))
            
            # Intent analysis
            kw_lower = keyword.lower()
            if any(word in kw_lower for word in ['buy', 'best', 'review', 'price']):
                intent = "🛒 Commercial Intent"
            elif any(word in kw_lower for word in ['how', 'what', 'guide', 'tips']):
                intent = "📚 Informational Intent"
            elif any(phrase in kw_lower for phrase in ['near me', 'local']):
                intent = "📍 Local Intent"
            else:
                intent = "🔍 General Search"
            
            st.info(f"**Intent Analysis:** {intent}")
            
        except Exception as e:
            st.warning("Analysis will be available after keyword selection")
        
        # Optional business context
        with st.expander("💡 Add business context for better strategy (optional)"):
            business_context = st.text_area(
                "What's your business about?",
                value=st.session_state.get("business_context", ""),
                placeholder="This helps create more targeted content strategy"
            )
            st.session_state.business_context = business_context
        
        if st.button("Create Strategy", type="primary"):
            st.session_state.selected_keyword = keyword
            state_manager.go_to_step(2)


# Flow 3: Custom Brief Flow
def render_custom_brief_flow(step):
    """Custom brief creation flow"""
    st.progress(step / 2) 
    st.caption(f"Step {step} of 2 - Custom Brief Path")
    
    if step == 1:
        render_custom_brief_creator()
    elif step == 2:
        render_brief_to_strategy()


def render_custom_brief_creator():
    """Custom brief creation interface"""
    st.markdown("### 📝 Create Your Content Brief")
    
    # Essential fields
    col1, col2 = st.columns(2)
    with col1:
        topic = st.text_input(
            "Content Topic:",
            value=st.session_state.get("custom_topic", ""),
            placeholder="Complete Guide to..."
        )
        audience = st.text_input(
            "Target Audience:",
            value=st.session_state.get("custom_audience", ""),
            placeholder="Small business owners"
        )
        
    with col2:
        content_type = st.selectbox(
            "Content Type:",
            ["Blog Post", "Landing Page", "Guide", "FAQ", "Email Series", "Case Study"],
            index=0
        )
        goal = st.selectbox(
            "Primary Goal:",
            ["Drive Traffic", "Generate Leads", "Educate", "Convert Sales", "Build Authority"],
            index=0
        )
    
    # Advanced options
    with st.expander("⚙️ Advanced Options"):
        tone = st.selectbox("Tone:", ["Professional", "Conversational", "Expert", "Friendly"], index=1)
        word_count = st.slider("Target Word Count:", 500, 5000, 2000, step=500)
        special_requirements = st.text_area(
            "Special Requirements:",
            placeholder="Any specific points to cover, competitors to mention, etc."
        )
    
    # Save data
    st.session_state.update({
        "custom_topic": topic,
        "custom_audience": audience,
        "custom_content_type": content_type,
        "custom_goal": goal,
        "custom_tone": tone,
        "custom_word_count": word_count,
        "custom_requirements": special_requirements
    })
    
    if topic and audience:
        brief_data = {
            "topic": topic,
            "audience": audience,
            "content_type": content_type,
            "goal": goal,
            "tone": tone,
            "word_count": word_count,
            "requirements": special_requirements
        }
        st.session_state.custom_brief_data = brief_data
        
        if st.button("Generate Brief & Strategy", type="primary"):
            state_manager.go_to_step(2)
    else:
        st.warning("Please provide at least a topic and target audience")


def render_brief_to_strategy():
    """Generate strategy from custom brief"""
    st.markdown("### 📋 Your Custom Content Strategy")
    
    brief_data = st.session_state.get("custom_brief_data", {})
    topic = brief_data.get("topic", "Custom Content")
    
    st.info(f"**Creating strategy for:** {topic}")
    
    if st.button("🚀 Generate Complete Strategy", type="primary"):
        with st.spinner("Creating your custom strategy..."):
            # Generate custom brief
            brief = generate_custom_brief(brief_data)
            st.session_state.generated_brief = brief
            
            # Optional competitive analysis
            competition_analysis = None
            if topic:
                try:
                    competition_analysis = analyze_competition_for_topic(topic)
                    st.session_state.competition_analysis = competition_analysis
                except:
                    pass
            
            # Generate action plan
            action_plan = generate_action_plan_custom(brief_data, brief, competition_analysis)
            st.session_state.action_plan = action_plan
    
    # Display results if generated
    if st.session_state.get("generated_brief"):
        tab1, tab2, tab3 = st.tabs(["📝 Your Brief", "🔍 Market Analysis", "🎯 Action Plan"])
        
        with tab1:
            st.markdown(st.session_state.generated_brief)
            
        with tab2:
            if st.session_state.get("competition_analysis"):
                st.markdown("#### Competitive Landscape")
                st.markdown(st.session_state.competition_analysis)
            else:
                st.info("💡 Tip: Adding a target keyword would enable competitive analysis")
                
        with tab3:
            st.markdown(st.session_state.get("action_plan", "Action plan will be generated..."))
            
        # Export options
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                "📥 Download Brief",
                data=st.session_state.generated_brief,
                file_name=f"brief_{topic.replace(' ', '_')}.md",
                mime="text/markdown"
            )
        with col2:
            complete_export = create_complete_export(
                st.session_state.generated_brief,
                st.session_state.get("competition_analysis", ""),
                st.session_state.get("action_plan", "")
            )
            st.download_button(
                "📋 Download Complete Strategy",
                data=complete_export,
                file_name="complete_strategy.md",
                mime="text/markdown"
            )


# Flow 4: Ideas Only Flow
def render_ideas_only_flow(step):
    """Content ideas and strategy generation"""
    st.progress(1.0)  # Single step
    st.caption("Content Ideas & Strategy Generator")
    
    render_ideas_generator()


def render_ideas_generator():
    """Generate content ideas and strategy"""
    st.markdown("### 💡 Content Ideas & Strategy Generator")
    
    # Quick context form
    col1, col2 = st.columns(2)
    with col1:
        niche = st.text_input(
            "What's your niche/industry?",
            value=st.session_state.get("ideas_niche", ""),
            placeholder="Digital marketing"
        )
    with col2:
        audience = st.text_input(
            "Who's your audience?",
            value=st.session_state.get("ideas_audience", ""),
            placeholder="Small business owners"
        )
    
    goals = st.multiselect(
        "What are your content goals?",
        ["Drive Traffic", "Generate Leads", "Build Authority", "Educate Audience", "Drive Sales"],
        default=st.session_state.get("ideas_goals", ["Drive Traffic"])
    )
    
    # Save inputs
    st.session_state.update({
        "ideas_niche": niche,
        "ideas_audience": audience,
        "ideas_goals": goals
    })
    
    if niche and st.button("Generate Ideas & Strategy", type="primary"):
        with st.spinner("Creating content ideas..."):
            ideas_strategy = generate_content_ideas_strategy(niche, audience, goals)
            st.session_state.ideas_strategy = ideas_strategy
    
    # Display results
    if st.session_state.get("ideas_strategy"):
        ideas_strategy = st.session_state.ideas_strategy
        
        tab1, tab2, tab3 = st.tabs(["💡 Content Ideas", "📅 Content Calendar", "🎯 Strategy"])
        
        with tab1:
            st.markdown("### Content Ideas")
            st.markdown(ideas_strategy.get("ideas", "No ideas generated yet"))
            
        with tab2:
            st.markdown("### 30-Day Content Calendar")
            st.markdown(ideas_strategy.get("calendar", "No calendar generated yet"))
            
        with tab3:
            st.markdown("### Content Strategy")
            st.markdown(ideas_strategy.get("strategy", "No strategy generated yet"))
            
            st.download_button(
                "📥 Download Complete Strategy",
                data=export_ideas_strategy(ideas_strategy),
                file_name=f"content_strategy_{niche.replace(' ', '_')}.md",
                mime="text/markdown"
            )


# Common strategy renderer
def render_complete_strategy():
    """Generate complete strategy for selected keyword"""
    st.markdown("### 🚀 Your Complete Content Strategy")
    
    selected_kw = st.session_state.get("selected_keyword")
    if not selected_kw:
        st.error("No keyword selected")
        return
    
    st.info(f"**Creating strategy for:** {selected_kw}")
    
    # Variant selection for AI-generated brief
    variant = st.radio("Choose brief variant:", ["A", "B"], horizontal=True)
    
    if st.button("🚀 Generate Complete Strategy", type="primary"):
        with st.spinner("Creating your complete strategy..."):
            # Generate brief
            brief_output, prompt, latency, usage = generate_brief_with_variant(
                keyword=selected_kw,
                variant=variant
            )
            st.session_state.brief_output = brief_output
            
            # Analyze competition (mock for now)
            serp_data = fetch_serp_snapshot(selected_kw)
            st.session_state.serp_data = serp_data
            
            # Generate action plan
            action_plan = generate_complete_action_plan(selected_kw, brief_output, serp_data)
            st.session_state.action_plan = action_plan
    
    # Display results
    if st.session_state.get("brief_output"):
        tab1, tab2, tab3 = st.tabs(["📝 Content Brief", "🔍 Competition", "🎯 Action Plan"])
        
        with tab1:
            st.markdown(st.session_state.brief_output)
            
        with tab2:
            serp_data = st.session_state.get("serp_data", [])
            st.markdown("#### 🏆 Top Competitors")
            for i, result in enumerate(serp_data[:5], 1):
                with st.expander(f"{i}. {result.get('title', 'No title')[:60]}..."):
                    st.write(f"**URL:** {result.get('url', 'N/A')}")
                    st.write(f"**Snippet:** {result.get('snippet', 'N/A')}")
            
        with tab3:
            st.markdown(st.session_state.get("action_plan", "Action plan generating..."))
            
            # Export button
            st.download_button(
                "📥 Download Complete Strategy",
                data=create_strategy_export(selected_kw),
                file_name=f"strategy_{selected_kw.replace(' ', '_')}.md",
                mime="text/markdown"
            )


# Helper functions
def generate_custom_brief(brief_data: Dict[str, Any]) -> str:
    """Generate custom brief from user data"""
    topic = brief_data.get("topic", "Content")
    audience = brief_data.get("audience", "Target audience")
    content_type = brief_data.get("content_type", "Blog Post")
    goal = brief_data.get("goal", "Educate")
    tone = brief_data.get("tone", "Professional")
    word_count = brief_data.get("word_count", 2000)
    
    return f"""# Content Brief: {topic}

## Overview
**Content Type:** {content_type}
**Target Audience:** {audience}
**Primary Goal:** {goal}
**Tone:** {tone}
**Target Length:** {word_count} words

## Content Structure
1. **Introduction**
   - Hook that resonates with {audience}
   - Clear value proposition
   - Preview of what they'll learn

2. **Main Content Sections**
   - [Section 1: Core concept explanation]
   - [Section 2: Practical applications]
   - [Section 3: Best practices and tips]
   - [Section 4: Common mistakes to avoid]

3. **Conclusion**
   - Summary of key points
   - Clear call-to-action aligned with {goal}

## SEO Optimization
- Primary keyword opportunities around "{topic}"
- Related keywords to naturally incorporate
- Meta title and description suggestions

## Additional Notes
{brief_data.get("requirements", "No additional requirements specified")}
"""


def generate_content_ideas_strategy(niche: str, audience: str, goals: List[str]) -> Dict[str, str]:
    """Generate content ideas and strategy"""
    goals_str = ", ".join(goals).lower()
    
    return {
        "ideas": f"""## Content Ideas for {niche}

### Blog Post Ideas
1. "Ultimate Guide to {niche} for {audience}"
2. "10 Common {niche} Mistakes {audience} Make"
3. "Case Study: How [Company] Achieved Success with {niche}"
4. "{niche} Tools and Resources Every {audience.rstrip('s')} Needs"
5. "Future of {niche}: Trends to Watch"

### Content Formats
- **How-to Guides**: Step-by-step tutorials
- **Comparison Posts**: Tool/service comparisons
- **Case Studies**: Real success stories
- **Resource Roundups**: Curated lists
- **FAQ Posts**: Common questions answered
""",
        
        "calendar": f"""## 30-Day Content Calendar

### Week 1: Foundation
- Day 1-2: "{niche} 101" introductory post
- Day 3-4: "Common Myths About {niche}" debunking post
- Day 5-7: Case study featuring successful {audience.rstrip('s')}

### Week 2: Practical Application
- Day 8-10: Step-by-step tutorial
- Day 11-12: Tools and resources roundup
- Day 13-14: FAQ compilation

### Week 3: Advanced Topics
- Day 15-17: Advanced strategies post
- Day 18-19: Industry trend analysis
- Day 20-21: Expert interview or guest post

### Week 4: Engagement & Community
- Day 22-24: Community-generated content
- Day 25-26: Behind-the-scenes content
- Day 27-30: Month recap and next month preview
""",
        
        "strategy": f"""## Content Strategy Overview

### Content Pillars
1. **Educational Content** (40%)
   - How-to guides and tutorials
   - Best practices and tips
   - Industry insights

2. **Community Content** (30%)
   - User-generated content
   - Success stories
   - Q&A sessions

3. **Product/Service Content** (20%)
   - Case studies
   - Feature highlights
   - Comparison content

4. **Brand Content** (10%)
   - Behind-the-scenes
   - Company culture
   - Thought leadership

### Distribution Strategy
- **Primary Platform**: Blog/Website
- **Social Media**: LinkedIn, Twitter for {audience}
- **Email Marketing**: Weekly newsletters
- **Community Engagement**: Industry forums and groups

### Success Metrics
Based on your goals ({goals_str}):
- Traffic growth: 20% month-over-month
- Lead generation: Track form submissions and downloads
- Engagement: Comments, shares, and time on page
- Authority building: Backlinks and mentions
"""
    }


def generate_complete_action_plan(keyword: str, brief: str, serp_data: List[Dict]) -> str:
    """Generate comprehensive action plan"""
    return f"""# Action Plan for "{keyword}"

## Immediate Actions (This Week)
1. **Content Creation**
   - Start with the content brief provided
   - Research top 3 competitors for content gaps
   - Create comprehensive outline

2. **Technical Setup**
   - Optimize page title and meta description
   - Ensure mobile-friendly design
   - Set up proper internal linking

## Short-term Goals (Next 30 Days)
1. **Content Development**
   - Publish main content piece
   - Create supporting content (FAQs, related posts)
   - Develop multimedia elements (images, videos)

2. **Promotion Strategy**
   - Share across social media channels
   - Reach out for backlink opportunities
   - Email to subscribers

## Long-term Strategy (3-6 Months)
1. **Content Optimization**
   - Monitor performance and update content
   - A/B test different headlines and CTAs
   - Expand based on user feedback

2. **Authority Building**
   - Guest posting on relevant sites
   - Building topic clusters around main keyword
   - Engaging with community discussions

## Success Metrics to Track
- Search ranking position for "{keyword}"
- Organic traffic growth
- User engagement (time on page, bounce rate)
- Conversion rates and lead generation
"""


def create_complete_export(brief: str, analysis: str, plan: str) -> str:
    """Create complete export document"""
    return f"""# Complete Content Strategy Export

{brief}

---

## Market Analysis
{analysis}

---

## Action Plan
{plan}

---

Generated by AI Keyword Strategy Tool
Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""


def export_ideas_strategy(ideas_strategy: Dict[str, str]) -> str:
    """Export ideas strategy as markdown"""
    return f"""# Content Strategy Export

{ideas_strategy.get("ideas", "")}

---

{ideas_strategy.get("calendar", "")}

---

{ideas_strategy.get("strategy", "")}

---

Generated by AI Keyword Strategy Tool
Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""


def create_strategy_export(keyword: str) -> str:
    """Create strategy export for keyword-based flow"""
    brief = st.session_state.get("brief_output", "")
    action_plan = st.session_state.get("action_plan", "")
    
    return f"""# Content Strategy: {keyword}

## Content Brief
{brief}

## Action Plan
{action_plan}

---

Generated by AI Keyword Strategy Tool
Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""


def generate_action_plan_custom(brief_data: Dict[str, Any], brief: str, competition_analysis: Optional[str]) -> str:
    """Generate action plan for custom brief"""
    topic = brief_data.get("topic", "Content")
    goal = brief_data.get("goal", "Educate")
    
    return f"""# Action Plan for "{topic}"

## Immediate Actions (This Week)
1. **Content Planning**
   - Review and refine the content brief
   - Create detailed content outline based on brief structure
   - Gather supporting materials (images, data, examples)

2. **Content Creation Setup**
   - Set up writing environment and templates
   - Schedule dedicated writing time
   - Identify key sources and references

## Short-term Goals (Next 30 Days)
1. **Content Development**
   - Write first draft following the brief structure
   - Create supporting multimedia content
   - Review and edit for {goal.lower()} effectiveness

2. **Optimization & Publishing**
   - Optimize for search engines and user experience
   - Set up proper formatting and structure
   - Prepare for publication and distribution

## Long-term Strategy (3-6 Months)
1. **Performance Monitoring**
   - Track content performance against {goal.lower()} metrics
   - Gather user feedback and engagement data
   - Update content based on performance insights

2. **Content Expansion**
   - Create related content based on performance
   - Develop content series or follow-up pieces
   - Build topical authority in this area

## Success Metrics to Track
- Goal-specific metrics for {goal.lower()}
- User engagement (time on page, shares, comments)
- Content performance indicators
- Audience growth and retention
"""


def analyze_competition_for_topic(topic: str) -> str:
    """Mock competition analysis for custom topics"""
    return f"""## Competition Analysis for "{topic}"

### Market Overview
The content landscape for "{topic}" shows moderate competition with opportunities for differentiation.

### Content Gaps Identified
1. **Depth**: Most existing content lacks comprehensive coverage
2. **Freshness**: Many top results are outdated (2+ years old)
3. **Format Diversity**: Limited use of multimedia and interactive elements
4. **User Experience**: Poor mobile optimization in several top results

### Opportunities
- Create more comprehensive, up-to-date content
- Include practical examples and case studies
- Develop interactive elements and multimedia
- Focus on user experience and page speed

### Recommended Approach
Position your content as the most comprehensive, up-to-date resource on "{topic}" with superior user experience and practical value.
"""