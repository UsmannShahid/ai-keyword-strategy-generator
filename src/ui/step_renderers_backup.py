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
    """Render the current step with unified linear navigation"""
    
    # Get current step
    current_step = st.session_state.get("ux_step", 1)
    
    # Render appropriate step
    if current_step == 1:
        render_step_1_business_input()
    elif current_step == 2:
        render_step_2_keywords()
    elif current_step == 3:
        render_step_3_brief()
    elif current_step == 4:
        render_step_4_serp()
    elif current_step == 5:
        render_step_5_suggestions()
    else:
        st.error(f"Invalid step: {current_step}")
        st.session_state.ux_step = 1


def render_step_1_business_input():
    """Step 1: Business input and context setting"""
    st.markdown("### 🏢 Step 1: Business Context")
    st.info("💡 Provide context about your business to generate targeted keyword suggestions.")
    
    seed_input = st.text_area(
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
    st.session_state.seed_input = seed_input
    st.session_state.industry_input = industry
    st.session_state.audience_input = target_audience
    
    if seed_input.strip():
        if st.button("🔍 Generate Keywords", type="primary"):
            state_manager.go_to_step(2)
    else:
        st.warning("Please describe your business to continue")


def render_step_2_keywords():
    """Step 2: AI keyword generation and selection"""
    st.markdown("### 🔑 Step 2: Keyword Selection")
    
    # Check if we have business context
    if not st.session_state.get("seed_input", "").strip():
        st.warning("Please complete Step 1 first.")
        if st.button("← Back to Business Context"):
            state_manager.go_to_step(1)
        return
    
    # Generate keywords if not already done
    if not st.session_state.get("keywords_data"):
        with st.spinner("Generating keywords..."):
            try:
                service = KeywordService()
                keywords_data = service.generate_keywords(
                    business_desc=st.session_state.seed_input,
                    industry=st.session_state.get("industry_input", ""),
                    audience=st.session_state.get("audience_input", "")
                )
                st.session_state.keywords_data = keywords_data
            except Exception as e:
                st.error(f"Error generating keywords: {str(e)}")
                return
    
    # Display keywords
    keywords_data = st.session_state.get("keywords_data", {})
    if not keywords_data:
        st.error("No keywords generated. Please try again.")
        return
    
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
                row = {"keyword": str(kw), "category": category}
            all_keywords.append(row)
    
    if all_keywords:
        df = pd.DataFrame(all_keywords)
        df = add_scores(df)  # Add realistic scores
        
        # Show top keywords
        st.markdown("#### 🎯 Generated Keywords")
        
        # Simple display without complex styling
        st.dataframe(df[["keyword", "category", "quick_win_score"]], use_container_width=True)
        
        # Selection
        keyword_options = df["keyword"].tolist()
        selected = st.selectbox("Select a keyword to continue:", [""] + keyword_options)
        
        if selected:
            kw_row = df[df["keyword"] == selected].iloc[0]
            st.info(f"**Selected:** {selected} (Score: {kw_row['quick_win_score']})")
            
            if st.button("📝 Generate Content Brief", type="primary"):
                st.session_state.selected_keyword = selected
                state_manager.go_to_step(3)
    
    # Navigation
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Back to Business Context"):
            state_manager.go_to_step(1)
    with col2:
        # Manual keyword entry option
        with st.expander("Or enter a keyword manually"):
            manual_kw = st.text_input("Enter keyword:", placeholder="e.g., best marketing software")
            if manual_kw and st.button("Use this keyword"):
                st.session_state.selected_keyword = manual_kw
                state_manager.go_to_step(3)


def render_step_3_brief():
    """Step 3: Content brief generation"""
    st.markdown("### 📝 Step 3: AI Content Brief")
    
    selected_kw = st.session_state.get("selected_keyword")
    if not selected_kw:
        st.warning("No keyword selected. Please complete Step 2 first.")
        if st.button("← Back to Keywords"):
            state_manager.go_to_step(2)
        return
    
    st.info(f"**Selected keyword:** {selected_kw}")
    
    # Variant selection
    variant = st.radio(
        "Choose brief format:",
        ["📋 Executive Summary", "📝 Detailed Guide"], 
        horizontal=True,
        help="Executive Summary = Key points & strategy overview | Detailed Guide = Step-by-step content instructions"
    )
    variant_letter = "A" if "Executive Summary" in variant else "B"  # Both are SEO-optimized
    
    if st.button("🚀 Generate Content Brief", type="primary"):
        with st.spinner("Generating content brief..."):
            try:
                brief_output, prompt, latency, usage = generate_brief_with_variant(
                    keyword=selected_kw,
                    variant=variant_letter
                )
                st.session_state.brief_output = brief_output
                st.session_state.brief_variant = variant_letter
                st.success("✅ Content brief generated successfully!")
                
                # Auto-advance to next step
                state_manager.go_to_step(4)
                
            except Exception as e:
                st.error(f"Error generating brief: {str(e)}")
    
    # Show generated brief if available
    if st.session_state.get("brief_output"):
        st.markdown("#### 📋 Generated Brief")
        with st.expander("View Content Brief", expanded=True):
            st.markdown(st.session_state.brief_output)
        
        # Navigation
        col1, col2 = st.columns(2)
        with col1:
            if st.button("← Back to Keywords"):
                state_manager.go_to_step(2)
        with col2:
            if st.button("Continue to SERP Analysis →"):
                state_manager.go_to_step(4)
    else:
        # Navigation
        if st.button("← Back to Keywords"):
            state_manager.go_to_step(2)


def render_step_4_serp():
    """Step 4: SERP Analysis"""
    st.markdown("### 🔍 Step 4: Competition Analysis")
    
    selected_kw = st.session_state.get("selected_keyword")
    if not selected_kw:
        st.warning("No keyword selected. Please complete previous steps.")
        if st.button("← Back to Brief"):
            state_manager.go_to_step(3)
        return
    
    st.info(f"**Analyzing competition for:** {selected_kw}")
    
    if st.button("🔍 Analyze Competition", type="primary"):
        with st.spinner("Analyzing search results..."):
            try:
                serp_data = fetch_serp_snapshot(selected_kw)
                st.session_state.serp_data = serp_data
                st.success("✅ Competition analysis completed!")
                
                # Auto-advance to suggestions
                state_manager.go_to_step(5)
                
            except Exception as e:
                st.error(f"Error analyzing competition: {str(e)}")
    
    # Show SERP data if available
    serp_data = st.session_state.get("serp_data", [])
    if serp_data:
        st.markdown("#### 🏆 Top Competitors")
        for i, result in enumerate(serp_data[:5], 1):
            with st.expander(f"{i}. {result.get('title', 'No title')[:60]}..."):
                st.write(f"**URL:** {result.get('url', 'N/A')}")
                st.write(f"**Snippet:** {result.get('snippet', 'N/A')}")
        
        # Navigation
        col1, col2 = st.columns(2)
        with col1:
            if st.button("← Back to Brief"):
                state_manager.go_to_step(3)
        with col2:
            if st.button("Get Strategy →"):
                state_manager.go_to_step(5)
    else:
        # Navigation
        if st.button("← Back to Brief"):
            state_manager.go_to_step(3)


def render_step_5_suggestions():
    """Step 5: Final Strategy and Export"""
    st.markdown("### 💡 Step 5: Your Complete Strategy")
    
    selected_kw = st.session_state.get("selected_keyword")
    brief_output = st.session_state.get("brief_output")
    serp_data = st.session_state.get("serp_data", [])
    
    if not selected_kw or not brief_output:
        st.warning("Please complete previous steps first.")
        if st.button("← Back to Competition Analysis"):
            state_manager.go_to_step(4)
        return
    
    st.success(f"✅ **Strategy ready for:** {selected_kw}")
    
    # Display final strategy components
    tab1, tab2, tab3 = st.tabs(["📝 Content Brief", "🔍 Competition", "🎯 Action Plan"])
    
    with tab1:
        st.markdown("#### Your Content Brief")
        st.markdown(brief_output)
        
    with tab2:
        st.markdown("#### Competition Analysis")
        if serp_data:
            for i, result in enumerate(serp_data[:3], 1):
                st.markdown(f"**{i}. {result.get('title', 'No title')}**")
                st.caption(f"URL: {result.get('url', 'N/A')}")
                st.write(result.get('snippet', 'N/A'))
                st.divider()
        else:
            st.info("No competition data available. Run Step 4 to analyze competitors.")
    
    with tab3:
        st.markdown("#### Recommended Action Plan")
        action_plan = generate_action_plan(selected_kw, brief_output, serp_data)
        st.markdown(action_plan)
    
    # Export options
    st.markdown("#### 📥 Export Your Strategy")
    col1, col2 = st.columns(2)
    
    with col1:
        # Download brief only
        st.download_button(
            "📄 Download Brief",
            data=brief_output,
            file_name=f"brief_{selected_kw.replace(' ', '_')}.md",
            mime="text/markdown",
            use_container_width=True
        )
    
    with col2:
        # Download complete strategy
        complete_strategy = create_complete_export(selected_kw, brief_output, serp_data)
        st.download_button(
            "📋 Download Complete Strategy",
            data=complete_strategy,
            file_name=f"strategy_{selected_kw.replace(' ', '_')}.md",
            mime="text/markdown",
            use_container_width=True
        )
    
    # Navigation
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Back to Competition"):
            state_manager.go_to_step(4)
    with col2:
        if st.button("🔄 Start New Analysis"):
            # Clear session and restart
            for key in ["selected_keyword", "brief_output", "serp_data", "keywords_data"]:
                if key in st.session_state:
                    del st.session_state[key]
            state_manager.go_to_step(1)


# Helper functions
def generate_action_plan(keyword: str, brief: str, serp_data: list) -> str:
    """Generate a simple action plan"""
    return f"""## Action Plan for "{keyword}"

### Immediate Actions (This Week)
1. **Content Creation**
   - Use the generated brief as your content outline
   - Research the top 3 competitors for content gaps
   - Create a comprehensive outline with H2/H3 structure

2. **Technical Setup**
   - Optimize page title and meta description from the brief
   - Ensure mobile-friendly design
   - Set up proper internal linking structure

### Short-term Goals (Next 30 Days)
1. **Content Development**
   - Write and publish the main content piece
   - Create supporting content (FAQs, related posts)
   - Add multimedia elements (images, videos, infographics)

2. **Promotion Strategy**
   - Share across your social media channels
   - Email to your subscriber list
   - Reach out for backlink opportunities from industry sites

### Long-term Strategy (3-6 Months)
1. **Content Optimization**
   - Monitor rankings and traffic for "{keyword}"
   - Update content based on performance data
   - A/B test different headlines and CTAs

2. **Authority Building**
   - Create related content to build topic clusters
   - Guest post on relevant industry websites
   - Engage with community discussions around this topic

### Success Metrics
- Search ranking position for "{keyword}"
- Organic traffic growth to the page
- User engagement metrics (time on page, bounce rate)
- Conversion rates and lead generation from this content"""


def create_complete_export(keyword: str, brief: str, serp_data: list) -> str:
    """Create a complete strategy export"""
    action_plan = generate_action_plan(keyword, brief, serp_data)
    
    competition_section = "## Competition Analysis\n\n"
    if serp_data:
        for i, result in enumerate(serp_data[:5], 1):
            competition_section += f"**{i}. {result.get('title', 'No title')}**\n"
            competition_section += f"URL: {result.get('url', 'N/A')}\n"
            competition_section += f"Snippet: {result.get('snippet', 'N/A')}\n\n"
    else:
        competition_section += "No competition data available.\n\n"
    
    from datetime import datetime
    return f"""# Complete Content Strategy: {keyword}

Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Content Brief
{brief}

---

{competition_section}

---

{action_plan}

---

*Generated by AI Keyword Strategy Tool*
"""
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