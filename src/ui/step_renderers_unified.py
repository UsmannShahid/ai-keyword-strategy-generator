"""
Step Renderers for the AI Keyword Tool - Unified Linear Navigation
Clean implementation with 5 linear steps
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
        "Choose brief style:",
        ["A - SEO Focused", "B - Writer Friendly"], 
        horizontal=True,
        help="A = Technical SEO brief, B = Easy-to-follow writer brief"
    )
    variant_letter = variant.split(" - ")[0]  # Extract A or B
    
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