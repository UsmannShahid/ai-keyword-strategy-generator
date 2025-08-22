"""
Step renderers for the AI Keyword Tool.
Extracted from app.py to improve maintainability.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from typing import List

from ..core.state_manager import state_manager, AppConfig
from ..core.prompt_manager import prompt_manager
from ..utils.scoring import add_scores, quickwin_breakdown, explain_quickwin
from ..core.services import generate_writer_notes, generate_brief_with_variant, fetch_serp_snapshot
from ..utils.parsing import parse_brief_output
from ..utils.brief_renderer import brief_to_markdown_full
from ..utils.serp_utils import analyze_serp
from ..utils.eval_logger import log_eval
from ..core.cache_manager import cache_manager, cached
from ..utils.db_utils import safe_save_session, safe_save_brief, safe_get_recent_sessions, safe_save_suggestion, safe_save_serp
import json


def _step_tip_popover(lines: List[str]):
    """Render a tip popover with given lines."""
    with st.popover("Need tips?"):
        for x in lines:
            st.markdown(f"- {x}")


def render_current_step():
    """Render the current step based on session state."""
    step = st.session_state.get("ux_step", 1)
    
    if step == 1:
        render_step_1_inputs()
    elif step == 2:
        render_step_2_keywords()
    elif step == 3:
        render_step_3_brief()
    elif step == 4:
        render_step_4_serp()
    elif step == 5:
        render_step_5_suggestions()


def render_step_1_inputs():
    """Render step 1: Input collection."""
    st.markdown("### 🧭 Step 1: Describe Your Business")
    
    # Input fields with proper vertical alignment
    st.markdown("""
    <style>
    .stTextInput > div > div > input {
        display: flex;
        align-items: center;
        padding: 0.75rem 1rem !important;
        line-height: 1.5 !important;
        height: auto !important;
        min-height: 2.75rem;
    }
    .stSelectbox > div > div > div {
        display: flex;
        align-items: center;
        min-height: 2.75rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.session_state.seed_input = st.text_input(
        "Business/Product Description",
        value=st.session_state.get("seed_input", ""),
        placeholder="e.g., eco-friendly yoga mats, online bookstore, mobile app development"
    )
    
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.industry_input = st.text_input(
            "Industry (optional)",
            value=st.session_state.get("industry_input", ""),
            placeholder="e.g., fitness, education, technology"
        )
    
    with col2:
        st.session_state.audience_input = st.text_input(
            "Target Audience (optional)",
            value=st.session_state.get("audience_input", ""),
            placeholder="e.g., busy professionals, college students"
        )
    
    col3, col4 = st.columns(2)
    with col3:
        st.session_state.country_input = st.selectbox(
            "Country",
            ["US", "UK", "CA", "AU", "DE", "FR", "ES", "IT"],
            index=0
        )
    
    with col4:
        st.session_state.language_input = st.selectbox(
            "Language",
            ["en", "es", "fr", "de", "it"],
            index=0
        )
    
    # Generate button
    if st.button("🔍 Generate Keywords", type="primary", disabled=not st.session_state.seed_input.strip()):
        with st.spinner("Generating keywords..."):
            from ..core.services import KeywordService
            service = KeywordService()
            keywords_data = service.generate_keywords(
                business_desc=st.session_state.seed_input,
                industry=st.session_state.industry_input,
                audience=st.session_state.audience_input,
                location=st.session_state.country_input
            )
            st.session_state.keywords_data = keywords_data
            state_manager.go_to_step(2)


def render_step_2_keywords():
    """Render step 2: Keyword selection."""
    st.markdown("### 🔎 Step 2: Choose Your Target Keyword")
    
    if not st.session_state.get("keywords_data"):
        st.warning("No keywords generated yet. Please go back to Step 1.")
        if st.button("← Back to Step 1"):
            state_manager.go_to_step(1)
        return
    
    # Display keywords with proper scoring and filtering
    keywords_data = st.session_state.keywords_data
    
    # Convert new format to dataframe
    all_keywords = []
    for category, kws in keywords_data.items():
        for kw in kws:
            if isinstance(kw, dict):
                # New format with scores
                row = {
                    "keyword": kw["keyword"],
                    "category": category,
                    "volume": kw.get("volume", 0),
                    "difficulty": kw.get("difficulty", 50),
                    "quick_win_score": kw.get("quick_win_score", 50)
                }
            else:
                # Old format - just strings
                row = {"keyword": kw, "category": category}
            all_keywords.append(row)
    
    if all_keywords:
        df = pd.DataFrame(all_keywords)
        df = add_scores(df)  # This will add scores if missing
        
        # Add score filtering
        col1, col2 = st.columns([3, 1])
        with col2:
            min_score = st.slider("Min Quick-Win Score", 0, 100, 60)
            
        # Filter by score
        filtered_df = df[df['quick_win_score'] >= min_score].copy()
        
        if filtered_df.empty:
            st.warning(f"No keywords with score >= {min_score}. Try lowering the threshold.")
            filtered_df = df.copy()
        
        # Color coding function with better contrast
        def color_by_score(row):
            score = row['quick_win_score']
            if score >= 80:
                return ['background-color: #dcfce7; color: #166534; font-weight: 500'] * len(row)  # Green with dark text
            elif score >= 60:
                return ['background-color: #fef3c7; color: #a16207; font-weight: 500'] * len(row)  # Yellow with dark text
            else:
                return ['background-color: #fee2e2; color: #b91c1c; font-weight: 500'] * len(row)  # Red with dark text
        
        # Display styled dataframe
        styled_df = filtered_df.style.apply(color_by_score, axis=1)
        st.dataframe(styled_df, use_container_width=True)
        
        # Show legend with better visual indicators
        st.markdown("""
        <div style="background: #f8fafc; padding: 12px; border-radius: 8px; border-left: 4px solid #3b82f6; margin: 16px 0;">
        <strong>🎯 Quick-Win Score Legend:</strong><br>
        <span style="background: #dcfce7; color: #166534; padding: 2px 8px; border-radius: 4px; margin-right: 8px;">🟢 80+ Excellent</span>
        <span style="background: #fef3c7; color: #a16207; padding: 2px 8px; border-radius: 4px; margin-right: 8px;">🟡 60-79 Good</span>
        <span style="background: #fee2e2; color: #b91c1c; padding: 2px 8px; border-radius: 4px;">🔴 <60 Challenging</span>
        </div>
        """, unsafe_allow_html=True)
        
        # Keyword selection
        keyword_options = filtered_df["keyword"].tolist()
        selected = st.selectbox("Select a keyword to generate content brief:", [""] + keyword_options)
        
        if selected:
            # Show selected keyword details
            kw_row = filtered_df[filtered_df["keyword"] == selected].iloc[0]
            st.info(f"**{selected}** • Score: {kw_row['quick_win_score']} • Volume: {kw_row['volume']} • Difficulty: {kw_row['difficulty']}")
            
            if st.button("📝 Generate Content Brief", type="primary"):
                st.session_state.selected_keyword = selected
                state_manager.go_to_step(3)
    
    # Navigation
    if st.button("← Back to Step 1"):
        state_manager.go_to_step(1)


def render_step_3_brief():
    """Render step 3: Content brief generation."""
    st.markdown("### 📝 Step 3: AI Content Brief")
    
    selected_kw = st.session_state.get("selected_keyword")
    if not selected_kw:
        st.warning("No keyword selected. Please go back to Step 2.")
        if st.button("← Back to Step 2"):
            state_manager.go_to_step(2)
        return
    
    st.info(f"**Selected keyword:** {selected_kw}")
    
    # Variant selection with explanation
    col1, col2 = st.columns(2)
    with col1:
        variant = st.radio("Choose variant:", ["A", "B"], horizontal=True)
    with col2:
        if variant == "A":
            st.caption("📋 **Variant A**: Structured SEO brief with technical details")
        else:
            st.caption("✍️ **Variant B**: Writer-friendly format with clear instructions")
    
    # Auto-generate brief for better flow
    auto_generate = st.checkbox("Auto-generate brief", value=True, help="Generate brief immediately when variant is selected")
    
    if auto_generate or st.button("🚀 Generate Content Brief", type="primary"):
        with st.spinner("Generating content brief..."):
            output, prompt, latency, usage = generate_brief_with_variant(
                keyword=selected_kw,
                variant=variant
            )
            st.session_state.brief_output = output
            st.session_state.brief_variant = variant
            st.session_state.brief_latency = latency
            st.session_state.brief_usage = usage
            
            # Save session and brief to database
            try:
                # Create a topic from the business description and keyword
                business_desc = st.session_state.get("seed_input", "")
                topic = f"{business_desc} - {selected_kw}" if business_desc else selected_kw
                
                session_id = safe_save_session(topic)
                if session_id and safe_save_brief(session_id, output):
                    st.session_state.current_session_id = session_id
                    st.success("✅ Brief saved to database!")
                else:
                    st.info("Brief generated successfully (database save skipped)")
            except Exception as e:
                st.warning(f"Brief generated but not saved to database: {str(e)}")
    
    # Display brief
    if st.session_state.get("brief_output"):
        st.markdown("#### Generated Brief")
        st.markdown(st.session_state.brief_output)
        
        # Show performance metrics
        if st.session_state.get("brief_latency"):
            st.caption(f"⚡ Generated in {st.session_state.brief_latency:.0f}ms")
        
        # Simplified action buttons
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                "📥 Download Brief",
                data=st.session_state.brief_output,
                file_name=f"brief_{selected_kw.replace(' ', '_')}.md",
                mime="text/markdown",
                use_container_width=True
            )
        with col2:
            if st.button("🔍 Continue to SERP Analysis", type="primary", use_container_width=True):
                state_manager.go_to_step(4)  # SERP analysis step
        
        # Simplified rating
        with st.expander("⭐ Rate this brief (optional)"):
            rating = st.slider("How useful is this brief?", 1, 5, 3)
            if st.button("Submit Rating"):
                log_eval({
                    "keyword": selected_kw,
                    "variant": variant,
                    "rating": rating,
                    "latency_ms": st.session_state.get("brief_latency", 0)
                })
                st.success("Thank you for your feedback!")
        
    
    # Navigation
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Back to Keywords"):
            state_manager.go_to_step(2)
    with col2:
        if st.button("🔄 Start Over"):
            # Clear session state
            for key in ["keywords_data", "selected_keyword", "brief_output", "show_rating"]:
                if key in st.session_state:
                    del st.session_state[key]
            state_manager.go_to_step(1)


def render_step_4_serp():
    """Render step 4: SERP analysis."""
    st.markdown("### 🔍 Step 4: SERP Analysis")
    
    selected_kw = st.session_state.get("selected_keyword")
    if not selected_kw:
        st.warning("No keyword selected.")
        if st.button("← Back to Brief"):
            state_manager.go_to_step(3)
        return
    
    st.info(f"**Analyzing SERP for:** {selected_kw}")
    
    # Auto-fetch SERP data if not already available
    if not st.session_state.get("serp_data"):
        with st.spinner("Fetching SERP data..."):
            serp_data = fetch_serp_snapshot(
                keyword=selected_kw,
                country=st.session_state.get("country_input", "US"),
                language=st.session_state.get("language_input", "en")
            )
            st.session_state.serp_data = serp_data
            
            # Save SERP data to database
            session_id = st.session_state.get("current_session_id")
            if session_id and serp_data:
                safe_save_serp(session_id, json.dumps(serp_data))
    
    # Display SERP results if available
    if st.session_state.get("serp_data"):
        serp_data = st.session_state.serp_data
        analysis = analyze_serp(serp_data)
        
        # Key metrics in a prominent box
        st.markdown("""
        <div style="background: #f8fafc; padding: 1.5rem; border-radius: 12px; border: 2px solid #e2e8f0; margin: 1rem 0;">
        <h4 style="margin: 0 0 1rem 0; color: #1e293b;">📊 SERP Overview</h4>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("🔍 Results Found", analysis['total_results'], help="Number of competing pages in search results")
        with col2:
            st.metric("🌐 Unique Domains", len(analysis['domains']), help="Different websites ranking (less = easier to rank)")
        with col3:
            st.metric("📝 Avg Title Length", f"{analysis['avg_title_length']:.0f} chars", help="Average title length of competitors")
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Competitor analysis in a clean layout
        st.markdown("#### 🏆 Top 5 Competitors")
        
        for i, result in enumerate(serp_data[:5], 1):
            # Create a card for each result
            st.markdown(f"""
            <div style="background: white; padding: 1rem; border-radius: 8px; border: 1px solid #e2e8f0; margin: 0.5rem 0;">
            <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
            <span style="background: #3b82f6; color: white; border-radius: 50%; width: 24px; height: 24px; display: inline-flex; align-items: center; justify-content: center; font-weight: bold; margin-right: 0.75rem; font-size: 12px;">{i}</span>
            <h5 style="margin: 0; color: #1e293b; font-size: 1rem;">{result['title'][:80]}{'...' if len(result['title']) > 80 else ''}</h5>
            </div>
            <p style="color: #10b981; font-size: 0.9rem; margin: 0.25rem 0;">{result['url']}</p>
            <p style="color: #64748b; font-size: 0.9rem; margin: 0.5rem 0 0 0; line-height: 1.4;">{result['snippet'][:120]}{'...' if len(result['snippet']) > 120 else ''}</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Clear opportunity analysis
        st.markdown("#### 💡 Content Opportunities")
        
        # Create tabs for different types of opportunities
        tab1, tab2, tab3 = st.tabs(["🎯 Quick Wins", "📈 Content Gaps", "🔧 Technical Tips"])
        
        with tab1:
            st.markdown("""
            **Immediate opportunities you can act on:**
            
            ✅ **Title Optimization**
            - Current avg title length: {:.0f} characters
            - Recommended: Keep titles 50-60 characters for mobile
            - Include your target keyword at the beginning
            
            ✅ **Content Depth**
            - Analyze if competitors have shallow content
            - Create more comprehensive, detailed guides
            - Add sections competitors are missing
            
            ✅ **User Experience**
            - Improve page loading speed
            - Add better navigation and structure
            - Include helpful visuals and examples
            """.format(analysis['avg_title_length']))
        
        with tab2:
            st.markdown("""
            **What competitors might be missing:**
            
            🔍 **Content Analysis**
            - Look for outdated information (check publish dates)
            - Find topics mentioned but not fully explained
            - Identify missing FAQ sections
            
            📊 **Format Opportunities**
            - Add comparison tables if competitors lack them
            - Create step-by-step guides
            - Include case studies and real examples
            
            🎥 **Media Gaps**
            - Add videos if competitors only have text
            - Create infographics for complex topics
            - Include interactive elements
            """)
        
        with tab3:
            st.markdown("""
            **Technical improvements for better ranking:**
            
            ⚡ **Performance**
            - Optimize for Core Web Vitals
            - Ensure mobile-first design
            - Improve loading speed
            
            🏗️ **Structure**
            - Use proper heading hierarchy (H1 > H2 > H3)
            - Add schema markup for rich snippets
            - Optimize internal linking
            
            📱 **User Signals**
            - Improve click-through rates with better titles
            - Reduce bounce rate with engaging content
            - Increase time on page with valuable information
            """)
        
        # Action button
        col1, col2 = st.columns([2, 1])
        with col1:
            if st.button("💡 Generate Detailed Content Strategy", type="primary", use_container_width=True):
                state_manager.go_to_step(5)  # Suggestions step
        with col2:
            if st.button("🔄 Refresh SERP", use_container_width=True):
                if "serp_data" in st.session_state:
                    del st.session_state["serp_data"]
                st.rerun()
    
    # Navigation
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Back to Brief"):
            state_manager.go_to_step(3)
    with col2:
        if st.button("🔄 Start Over"):
            for key in ["keywords_data", "selected_keyword", "brief_output", "serp_data"]:
                if key in st.session_state:
                    del st.session_state[key]
            state_manager.go_to_step(1)


def render_step_5_suggestions():
    """Render step 5: Content suggestions."""
    st.markdown("### 💡 Step 5: Content Strategy Suggestions")
    
    selected_kw = st.session_state.get("selected_keyword")
    serp_data = st.session_state.get("serp_data", [])
    session_id = st.session_state.get("current_session_id")
    
    if not selected_kw:
        st.warning("No keyword selected.")
        if st.button("← Back to SERP"):
            state_manager.go_to_step(4)
        return
    
    st.success(f"**Strategy for:** {selected_kw}")
    
    # Generate and save AI suggestions if not already done
    if not st.session_state.get("ai_suggestions_generated"):
        with st.spinner("Generating AI-powered content suggestions..."):
            # Generate quick wins suggestions
            quick_wins = f"""**Quick-Win Opportunities for "{selected_kw}":**

🚀 **Immediate Actions:**
• Target long-tail variations: "{selected_kw} guide", "{selected_kw} tips", "best {selected_kw}"
• Create FAQ sections addressing common {selected_kw} questions
• Optimize for featured snippet opportunities with structured data
• Add comparison tables if competitors lack them

📈 **Content Gaps to Fill:**
• Update outdated information in competitor {selected_kw} content
• Add missing multimedia (images, videos, infographics) about {selected_kw}
• Create more comprehensive {selected_kw} guides
• Address specific user pain points related to {selected_kw}"""

            # Generate content ideas
            content_ideas = f"""**Content Ideas for "{selected_kw}":**

� **Primary Content:**
• Ultimate guide to {selected_kw}
• {selected_kw}: Beginner's complete tutorial  
• Common {selected_kw} mistakes to avoid
• {selected_kw} best practices and tips

🔄 **Supporting Content:**
• {selected_kw} vs alternatives comparison
• {selected_kw} case studies and examples
• {selected_kw} tools and resources roundup
• How to choose the right {selected_kw}

🎥 **Multimedia Opportunities:**
• Step-by-step {selected_kw} video tutorial
• {selected_kw} infographic or cheat sheet
• Interactive {selected_kw} calculator or tool
• {selected_kw} before/after showcase"""

            # Generate technical SEO suggestions
            technical_seo = f"""**Technical SEO Checklist for "{selected_kw}":**

✅ **On-Page Optimization:**
• Include "{selected_kw}" in title tag (front-loaded)
• Use "{selected_kw}" in H1 and at least one H2
• Add "{selected_kw}" to meta description naturally
• Include related keywords: "{selected_kw} guide", "{selected_kw} tips"

✅ **User Experience:**
• Ensure fast page load speed (<3 seconds)
• Make {selected_kw} content mobile-friendly
• Add clear navigation and internal links
• Include table of contents for long {selected_kw} content

✅ **Content Structure:**
• Use proper heading hierarchy (H1 > H2 > H3)
• Add schema markup for {selected_kw} content
• Include relevant {selected_kw} images with alt text
• Create engaging meta descriptions about {selected_kw}"""

            # Save suggestions to database
            if session_id:
                safe_save_suggestion(session_id, quick_wins, "quick_wins")
                safe_save_suggestion(session_id, content_ideas, "content_ideas")
                safe_save_suggestion(session_id, technical_seo, "technical_seo")
            
            # Store in session state
            st.session_state.ai_suggestions = {
                "quick_wins": quick_wins,
                "content_ideas": content_ideas,
                "technical_seo": technical_seo
            }
            st.session_state.ai_suggestions_generated = True
    
    # Display the suggestions
    suggestions = st.session_state.get("ai_suggestions", {})
    
    # Content suggestions based on SERP analysis
    st.markdown("#### 🎯 AI-Generated Content Strategy")
    
    tabs = st.tabs(["Quick Wins", "Content Ideas", "Technical SEO", "Next Steps"])
    
    with tabs[0]:
        if "quick_wins" in suggestions:
            st.markdown(suggestions["quick_wins"])
        else:
            st.markdown("Loading quick wins suggestions...")
    
    with tabs[1]:
        if "content_ideas" in suggestions:
            st.markdown(suggestions["content_ideas"])
        else:
            st.markdown("Loading content ideas...")
    
    with tabs[2]:
        if "technical_seo" in suggestions:
            st.markdown(suggestions["technical_seo"])
        else:
            st.markdown("Loading technical SEO suggestions...")
    
    with tabs[3]:
        st.markdown("""
        **Next Steps:**
        
        🗓️ **Content Calendar:**
        1. **Week 1:** Create primary content piece
        2. **Week 2:** Develop supporting content
        3. **Week 3:** Build internal linking structure
        4. **Week 4:** Monitor and optimize based on performance
        
        📊 **Success Metrics to Track:**
        • Organic traffic growth for target keyword
        • SERP ranking position improvements
        • Click-through rate from search results
        • User engagement metrics (time on page, bounce rate)
        
        🔄 **Optimization Cycle:**
        • Publish content → Monitor performance → Gather feedback → Iterate and improve
        """)
    
    # Final actions
    st.markdown("#### 🚀 Ready to Execute?")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.download_button(
            "📋 Download Full Strategy",
            data=f"# Content Strategy for '{selected_kw}'\n\n" + "[Complete strategy content here]",
            file_name=f"strategy_{selected_kw.replace(' ', '_')}.md",
            mime="text/markdown"
        ):
            st.success("Strategy downloaded!")
    
    with col2:
        if st.button("📊 View Analytics"):
            st.info("Connect your analytics tool to track progress!")
    
    with col3:
        if st.button("🔄 New Analysis"):
            for key in list(st.session_state.keys()):
                if key.startswith(("keywords_", "selected_", "brief_", "serp_")):
                    del st.session_state[key]
            state_manager.go_to_step(1)
    
    # Navigation
    if st.button("← Back to SERP Analysis"):
        state_manager.go_to_step(4)