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
    from ..core.services import KeywordService, generate_brief_with_variant, fetch_serp_snapshot, check_keyword_analysis_availability
    from ..utils.scoring import add_scores, analyze_keyword
    from ..utils.db_utils import safe_save_session, safe_save_brief
except ImportError:
    # Fallback for missing imports
    class SimpleStateManager:
        def go_to_step(self, step: int):
            st.session_state.ux_step = step
    state_manager = SimpleStateManager()


def render_progress_indicator(current_step, total_steps=5):
    """Enhanced progress bar with time estimates"""
    
    # Visual progress bar
    progress = current_step / total_steps
    st.progress(progress)
    
    # Step information with time estimates
    steps_info = {
        1: ("📝 Business Info", "2 min"),
        2: ("🔍 Find Keywords", "3 min"), 
        3: ("📋 Content Plan", "2 min"),
        4: ("🔍 Competition", "1 min"),
        5: ("🚀 Strategy", "1 min")
    }
    
    # Create columns for breadcrumb navigation
    cols = st.columns(total_steps)
    for i, (col, (step_name, time_est)) in enumerate(zip(cols, steps_info.items()), 1):
        with col:
            if i < current_step:
                st.success(f"✅ {step_name}")
            elif i == current_step:
                st.info(f"🔄 {step_name}\n⏱️ ~{time_est}")
            else:
                st.caption(f"⏳ {step_name}\n⏱️ ~{time_est}")
    
    # Total time remaining
    time_estimates = [2, 3, 2, 1, 1]
    remaining_time = sum(time_estimates[current_step-1:])
    if remaining_time > 0:
        st.caption(f"⏱️ Estimated time remaining: ~{remaining_time} minutes")
    
    st.divider()


def render_contextual_help_sidebar():
    """Add helpful tips in sidebar based on current step"""
    current_step = st.session_state.get("ux_step", 1)
    
    with st.sidebar:
        st.markdown("### 💡 Quick Tips")
        
        if current_step == 1:
            tips = [
                "Be specific about your services and target customers",
                "Mention your location for local SEO benefits", 
                "Include what makes you different from competitors"
            ]
        elif current_step == 2:
            tips = [
                "Start with keywords scoring 70+ for quick wins",
                "Look for 1000+ monthly searches for good traffic",
                "Lower competition % means easier ranking",
                "Mix short and long-tail keywords"
            ]
        elif current_step == 3:
            tips = [
                "Your content brief will guide your writing",
                "Include your target keyword naturally",
                "Focus on solving customer problems"
            ]
        elif current_step == 4:
            tips = [
                "Study competitor content gaps",
                "Look for outdated information to update",
                "Find opportunities to create better content"
            ]
        else:
            tips = [
                "Download your strategy for reference",
                "Start with the highest-priority keywords",
                "Track your progress over time"
            ]
        
        for tip in tips:
            st.info(f"💡 {tip}")
        
        # Add quick actions for power users
        if current_step >= 2:
            st.markdown("### ⚡ Quick Actions")
            
            # Quick start examples
            if st.button("🚀 Example: Restaurant"):
                st.session_state.seed_input = "Local Italian restaurant serving authentic pasta and pizza to families and couples in downtown area"
                st.session_state.industry_input = "Restaurant & Food"
                st.session_state.audience_input = "Local families, couples, food lovers"
                st.rerun()
                
            if st.button("🚀 Example: Fitness"):
                st.session_state.seed_input = "Personal training studio helping busy professionals get fit with 30-minute HIIT workouts and nutrition coaching"
                st.session_state.industry_input = "Health & Fitness"
                st.session_state.audience_input = "Busy professionals, working parents"
                st.rerun()


def detect_industry_from_description(business_desc: str) -> str:
    """AI-powered industry detection from business description"""
    business_lower = business_desc.lower()
    
    industry_keywords = {
        "Restaurant & Food": ["restaurant", "cafe", "food", "kitchen", "dining", "catering", "bakery"],
        "Health & Fitness": ["gym", "fitness", "health", "medical", "doctor", "clinic", "wellness"],
        "Technology": ["software", "app", "tech", "digital", "website", "coding", "development"],
        "Real Estate": ["real estate", "property", "housing", "rental", "mortgage", "realtor"],
        "Education": ["school", "education", "learning", "training", "course", "teaching"],
        "Retail & E-commerce": ["shop", "store", "retail", "online", "ecommerce", "selling"],
        "Professional Services": ["consulting", "legal", "accounting", "financial", "marketing", "agency"]
    }
    
    for industry, keywords in industry_keywords.items():
        if any(keyword in business_lower for keyword in keywords):
            return industry
    
    return ""


def render_smart_business_input():
    """Enhanced business input with real-time guidance"""
    
    st.markdown("### 📝 Tell Us About Your Business")
    st.info("💡 Help us understand what you do so we can find the best keywords for you.")
    
    # Business description with enhanced guidance
    business_desc = st.text_area(
        "What does your business do?",
        value=st.session_state.get("seed_input", ""),
        height=120,
        placeholder="e.g., We help small restaurants get more customers through social media and Google reviews. We create posts, manage ads, and help them get found online.",
        help="💡 Be specific about your services, target customers, and unique value proposition"
    )
    
    # Real-time feedback on description quality
    char_count = len(business_desc.strip())
    if char_count < 50:
        st.warning(f"💡 Add more details ({char_count}/50+ characters) - describe your services and target customers")
    elif char_count < 100:
        st.info(f"👍 Good start! ({char_count} characters) - Consider adding your unique value proposition")
    else:
        st.success(f"✅ Excellent description! ({char_count} characters)")
    
    # Auto-detect industry and show suggestion
    if char_count > 20:
        detected_industry = detect_industry_from_description(business_desc)
        if detected_industry:
            st.caption(f"💡 Detected industry: **{detected_industry}**")
    
    return business_desc


def render_current_step():
    """Render the current step - clean version without duplicate progress bars"""
    
    # No duplicate progress indicators - handled by app.py step_header
    # No duplicate sidebar help - handled by app.py sidebar
    
    # Get selected workflow
    workflow = st.session_state.get("selected_workflow", "keyword_research")
    
    # Render the appropriate workflow
    if workflow == "keyword_research":
        render_keyword_research_workflow()
    elif workflow == "content_strategy":
        render_content_strategy_workflow()
    elif workflow == "content_outline":
        render_content_outline_workflow()
    elif workflow == "content_ideas":
        render_content_ideas_workflow()
    elif workflow == "quick_brief":
        render_quick_brief_workflow()
    else:
        # Default to keyword research
        st.session_state.selected_workflow = "keyword_research"
        render_keyword_research_workflow()


def render_dashboard_sidebar():
    """Sidebar navigation is handled by app.py to avoid duplication"""
    # The main sidebar with workflow navigation is rendered in app.py
    # This function exists for compatibility but doesn't add duplicate sidebar content
    pass


def render_main_header(workflow_info, current_step=None, total_steps=None):
    """Render minimal workflow header - main header is handled by app.py"""
    workflow_id, icon, title, description = workflow_info
    
    # Simple workflow title and reset button
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown(f"## {icon} {title}")
        st.caption(description)
    with col2:
        if st.button("🔄 Reset Workflow", key="header_reset", help="Start this workflow over"):
            # Reset workflow-specific state
            workflow_keys = ["ux_step", "selected_keyword", "brief_output", "serp_data", "keywords_data"]
            for key in workflow_keys:
                if key in st.session_state:
                    del st.session_state[key]
            st.session_state.ux_step = 1
            st.rerun()
    
    st.divider()


def render_keyword_research_workflow():
    """Render the full keyword research workflow (original 5-step process)"""
    # Get current step
    current_step = st.session_state.get("ux_step", 1)
    
    # Render main header
    workflow_info = ("keyword_research", "🔍", "Keyword Research", "Full SEO keyword analysis & strategy")
    render_main_header(workflow_info, current_step, 5)
    
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
    # Use the smart business input with enhanced UX
    seed_input = render_smart_business_input()
    
    # Optional additional context with simpler language
    col1, col2, col3 = st.columns(3)
    with col1:
        industry = st.text_input(
            "What industry? (optional):",
            value=st.session_state.get("industry_input", ""),
            placeholder="e.g., Restaurants, Fitness, Real Estate"
        )
    with col2:
        target_audience = st.text_input(
            "Who are your customers? (optional):",
            value=st.session_state.get("audience_input", ""),
            placeholder="e.g., Busy parents, Local businesses"
        )
    with col3:
        country_options = {
            "US": "🇺🇸 United States",
            "CA": "🇨🇦 Canada",
            "GB": "🇬🇧 United Kingdom", 
            "AU": "🇦🇺 Australia",
            "DE": "🇩🇪 Germany",
            "FR": "🇫🇷 France",
            "ES": "🇪🇸 Spain",
            "IT": "🇮🇹 Italy",
            "NL": "🇳🇱 Netherlands",
            "BR": "🇧🇷 Brazil",
            "MX": "🇲🇽 Mexico",
            "JP": "🇯🇵 Japan",
            "IN": "🇮🇳 India",
            "SG": "🇸🇬 Singapore"
        }
        
        current_country = st.session_state.get("country_input", "US")
        country = st.selectbox(
            "Target Country:",
            options=list(country_options.keys()),
            index=list(country_options.keys()).index(current_country) if current_country in country_options else 0,
            format_func=lambda x: country_options[x],
            help="Choose your primary target market for localized keyword research"
        )
    
    # Save to session state
    st.session_state.seed_input = seed_input
    st.session_state.industry_input = industry
    st.session_state.audience_input = target_audience
    st.session_state.country_input = country
    
    # Smart defaults and suggestions
    if len(seed_input.strip()) > 20:
        detected_industry = detect_industry_from_description(seed_input)
        if detected_industry and not industry:
            st.caption(f"💡 Try setting industry to: **{detected_industry}**")
    
    # Always show the button - better UX with disabled state
    has_input = seed_input.strip()
    if has_input:
        if st.button("🔍 Generate Keywords", type="primary"):
            state_manager.go_to_step(2)
        st.info("👀 **Next:** We'll find keywords that your potential customers are searching for")
    else:
        st.button(
            "🔍 Generate Keywords", 
            type="primary",
            disabled=True,
            help="Complete business description above to enable keyword generation"
        )
        st.caption("⬆️ Fill in business details above to activate keyword generation")
        st.info("📝 **What happens next:** Tell us about your business → Find great keywords → Create content plan → Get more customers")


def render_step_2_keywords():
    """Step 2: AI keyword generation and selection"""
    st.markdown("### 🔍 Find Your Best Keywords")
    
    # Show selected country context
    country = st.session_state.get("country_input", "US")
    country_names = {
        "US": "🇺🇸 United States", "CA": "🇨🇦 Canada", "GB": "🇬🇧 United Kingdom", 
        "AU": "🇦🇺 Australia", "DE": "🇩🇪 Germany", "FR": "🇫🇷 France",
        "ES": "🇪🇸 Spain", "IT": "🇮🇹 Italy", "NL": "🇳🇱 Netherlands",
        "BR": "🇧🇷 Brazil", "MX": "🇲🇽 Mexico", "JP": "🇯🇵 Japan",
        "IN": "🇮🇳 India", "SG": "🇸🇬 Singapore"
    }
    st.info(f"🌍 **Target Market:** {country_names.get(country, country)} | Keywords optimized for this region")
    
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
                    audience=st.session_state.get("audience_input", ""),
                    country=st.session_state.get("country_input", "US"),
                    plan_settings=st.session_state.get('plan_settings', {})
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
        
        # Show enhanced keyword table for non-SEO experts
        st.markdown("#### 🎯 Your Keyword Opportunities")
        
        # Add contextual help expander
        with st.expander("🤔 How to read this table"):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("""
                **🔍 Keyword**: What people search for
                **📋 Type**: Category of search intent
                **👥 Searches**: Monthly search volume
                """)
            with col2:
                st.markdown("""
                **⚡ Comp**: Competition level (lower = easier)
                **🎯 Score**: Opportunity rating
                - 🟢 70+ = Quick wins (easy to rank)
                - 🟡 50-69 = Medium effort  
                - 🔴 <50 = Challenging (high competition)
                """)
        
        st.caption("💡 **Green = Easy wins** | **Yellow = Medium effort** | **Red = Hard to rank**")
        
        # Enhanced dataframe with color coding and more columns
        display_df = df.copy()
        
        # Add user-friendly columns
        if 'volume' not in display_df.columns:
            display_df['volume'] = [1000, 2000, 500, 1500, 800] * (len(display_df) // 5 + 1)
            display_df = display_df.iloc[:len(df)]
        
        if 'difficulty' not in display_df.columns:
            display_df['difficulty'] = [30, 45, 25, 55, 35] * (len(display_df) // 5 + 1)
            display_df = display_df.iloc[:len(df)]
        
        # Rename columns for non-SEO experts - shorter names for better fit
        display_df = display_df.rename(columns={
            'keyword': 'Keyword',
            'category': 'Type',
            'volume': 'Searches',
            'difficulty': 'Comp %',
            'quick_win_score': 'Score'
        })
        
        # Color coding function for opportunity score
        def color_score(val):
            if val >= 70:
                return 'background-color: #d1fae5; color: #065f46'  # Green
            elif val >= 50:
                return 'background-color: #fef3c7; color: #92400e'  # Yellow
            else:
                return 'background-color: #fee2e2; color: #991b1b'  # Red
        
        # Apply styling - use map instead of deprecated applymap
        styled_df = display_df.style.map(color_score, subset=['Score'])
        
        # Display the enhanced table with compact configuration
        st.dataframe(
            styled_df,
            use_container_width=True,
            height=400,  # Fixed height to fit on screen
            column_config={
                "Keyword": st.column_config.TextColumn("🔍 Keyword", width="medium"),
                "Type": st.column_config.TextColumn("📋 Type", width="small"),
                "Searches": st.column_config.NumberColumn("👥 Searches/mo", format="%d", width="small"),
                "Comp %": st.column_config.NumberColumn("⚡ Comp", format="%d%%", width="small"),
                "Score": st.column_config.NumberColumn("🎯 Score", format="%d", width="small")
            },
            hide_index=True
        )
        
        # Compact explanation
        st.info("� **Quick Guide:** Searches = monthly volume, Comp = competition %, Score = opportunity (70+ = easy wins)")
        
        # Selection with always-visible button  
        keyword_options = df["keyword"].tolist()
        selected = st.selectbox("Choose your target keyword:", [""] + keyword_options)
        
        # Always show the Generate Brief button
        if selected:
            kw_row = df[df["keyword"] == selected].iloc[0]
            score = kw_row.get('quick_win_score', 50)
            searches = kw_row.get('volume', 1000)
            
            # Color-coded success message
            if score >= 70:
                st.success(f"🎯 **Great Choice!** {selected}")
                st.caption(f"✅ High opportunity (Score: {score}) • {searches:,} monthly searches")
            elif score >= 50:
                st.warning(f"🎯 **Good Choice!** {selected}")  
                st.caption(f"⚡ Medium opportunity (Score: {score}) • {searches:,} monthly searches")
            else:
                st.error(f"🎯 **Challenging Choice!** {selected}")
                st.caption(f"⚠️ Low opportunity (Score: {score}) • {searches:,} monthly searches")
            
            if st.button("📝 Generate Content Brief", type="primary"):
                st.session_state.selected_keyword = selected
                state_manager.go_to_step(3)
            st.info("👀 **Next:** Create a detailed content plan to help you write great content that people will find")
        else:
            st.button(
                "📝 Generate Content Brief", 
                type="primary",
                disabled=True,
                help="Select a keyword from the table above to enable brief generation"
            )
            st.caption("👆 Choose a keyword above to create your content plan")
            st.info("💡 **Tip:** Pick keywords with high Opportunity Scores (green = best) and good monthly search numbers")
        
        # Google Keyword Planner (GKP) Data Integration
        st.divider()
        st.markdown("#### 📋 Google Keyword Planner Suggestions")
        
        # Import GKP functions
        from ..core.keywords import load_gkp_keywords, get_keyword_stats, format_keyword_for_display
        
        plan_settings = st.session_state.get('plan_settings', {})
        user_topic = st.session_state.get("seed_input", "")
        
        if user_topic:
            # Load GKP keywords based on user topic and plan
            max_suggestions = plan_settings.get("max_keywords", 20) if plan_settings else 20
            
            try:
                gkp_keywords = load_gkp_keywords(
                    topic=user_topic,
                    max_results=max_suggestions,
                    plan_settings=plan_settings
                )
                
                if gkp_keywords:
                    # Show statistics
                    stats = get_keyword_stats(gkp_keywords)
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("GKP Keywords", stats.get('total_keywords', 0))
                    with col2:
                        st.metric("Avg Volume", f"{stats.get('avg_volume', 0):,.0f}")
                    with col3:
                        st.metric("Avg Competition", f"{stats.get('avg_competition', 0):.0%}")
                    with col4:
                        st.metric("Avg CPC", f"${stats.get('avg_cpc', 0):.2f}")
                    
                    # Display keywords
                    st.markdown("**Keyword Suggestions from Google Keyword Planner:**")
                    
                    # Show different number based on plan
                    display_limit = min(len(gkp_keywords), 10 if plan_settings.get('user_plan') == 'free' else 20)
                    
                    for i, kw in enumerate(gkp_keywords[:display_limit]):
                        formatted_kw = format_keyword_for_display(kw)
                        
                        # Add selection button for each keyword
                        col_kw, col_btn = st.columns([4, 1])
                        with col_kw:
                            st.markdown(formatted_kw)
                        with col_btn:
                            if st.button("Select", key=f"gkp_{i}", help=f"Use '{kw.get('Keyword', '')}' for content brief"):
                                st.session_state.selected_keyword = kw.get('Keyword', '')
                                st.session_state.selected_keyword_source = "Google Keyword Planner"
                                st.success(f"✅ Selected: {kw.get('Keyword', '')}")
                                state_manager.go_to_step(3)
                    
                    # Plan-specific messaging
                    if plan_settings.get('user_plan') == 'free' and len(gkp_keywords) > 10:
                        st.info(f"🆓 **Free Plan** - Showing 10 of {len(gkp_keywords)} available keywords")
                        st.caption("💎 Upgrade to Premium to see all keyword suggestions")
                    
                    # Data source attribution
                    st.caption("📊 Data source: Google Keyword Planner")
                    
                else:
                    st.info(f"No Google Keyword Planner data found for '{user_topic}'. Try a broader topic.")
                    
            except Exception as e:
                st.error(f"Error loading GKP keywords: {str(e)}")
                st.caption("Using AI-generated keywords instead.")
        else:
            st.info("Enter a business topic above to see Google Keyword Planner suggestions.")
        
        # AI Keyword Analysis Demo (Plan-Based Feature)
        st.divider()
        st.markdown("#### 🧠 AI Keyword Analysis & Clustering")
        
        # Import the analysis functions
        from ..core.services import analyze_keywords_with_gpt, show_analysis, check_keyword_analysis_availability
        from ..core.keywords import load_gkp_keywords
        
        plan_settings = st.session_state.get('plan_settings', {})
        
        if check_keyword_analysis_availability(plan_settings):
            st.success("✅ **Premium Feature Available** - Advanced AI analysis enabled")
            
            # Choose analysis source
            analysis_source = st.radio(
                "Choose keywords to analyze:",
                ["🤖 AI-Generated Keywords", "📊 Google Keyword Planner Data", "🔀 Combined Analysis"],
                horizontal=True,
                help="Select which keyword dataset to analyze with GPT"
            )
            
            if st.button("🔍 Analyze Keywords with AI", type="secondary"):
                with st.spinner("Running GPT analysis..."):
                    try:
                        keywords_to_analyze = []
                        
                        if analysis_source == "🤖 AI-Generated Keywords":
                            # Use AI-generated keywords
                            keywords_data = st.session_state.get("keywords_data", {})
                            keywords_to_analyze = keywords_data
                            
                        elif analysis_source == "📊 Google Keyword Planner Data":
                            # Use GKP keywords
                            user_topic = st.session_state.get("seed_input", "")
                            country = st.session_state.get("country_input", "US")
                            if user_topic:
                                gkp_keywords = load_gkp_keywords(
                                    topic=f"{user_topic} {country}",  # Include country context
                                    max_results=plan_settings.get("max_keywords", 20),
                                    plan_settings=plan_settings
                                )
                                keywords_to_analyze = gkp_keywords
                            else:
                                st.error("No topic provided for GKP analysis")
                                keywords_to_analyze = []
                                
                        else:  # Combined Analysis
                            # Combine both AI and GKP keywords
                            ai_keywords_data = st.session_state.get("keywords_data", {})
                            user_topic = st.session_state.get("seed_input", "")
                            
                            combined_keywords = []
                            
                            # Add AI keywords
                            if ai_keywords_data:
                                for category, kws in ai_keywords_data.items():
                                    for kw in kws:
                                        if isinstance(kw, dict):
                                            kw['source'] = 'AI Generated'
                                            combined_keywords.append(kw)
                                        else:
                                            combined_keywords.append({
                                                "Keyword": str(kw),
                                                "Search Volume": 1000,
                                                "Competition": 0.5,
                                                "CPC": 1.0,
                                                "source": "AI Generated"
                                            })
                            
                            # Add GKP keywords
                            if user_topic:
                                country = st.session_state.get("country_input", "US")
                                gkp_keywords = load_gkp_keywords(
                                    topic=f"{user_topic} {country}",  # Include country context
                                    max_results=10,  # Limit to avoid overwhelming
                                    plan_settings=plan_settings
                                )
                                for kw in gkp_keywords:
                                    kw['source'] = 'Google Keyword Planner'
                                    combined_keywords.append(kw)
                            
                            keywords_to_analyze = combined_keywords
                        
                        if keywords_to_analyze:
                            ai_analysis = analyze_keywords_with_gpt(keywords_to_analyze, plan_settings)
                            show_analysis(ai_analysis)
                        else:
                            st.error("No keywords available for analysis")
                            
                    except Exception as e:
                        st.error(f"Analysis error: {str(e)}")
                        
        else:
            st.warning("🔒 **Premium Feature** - Advanced keyword analysis with AI insights")
            st.info("💎 Upgrade to Premium to unlock:")
            st.markdown("""
            - 🤖 **GPT-4 powered keyword clustering** by search intent
            - 🎯 **Quick Win identification** (low competition + high volume)
            - 📈 **Competitive analysis** and opportunity assessment  
            - 💡 **Strategic content recommendations** and priority ranking
            - 🔄 **Analysis of both AI and GKP keyword data**
            """)

    # Quick Win Full Flow (Premium Feature)
    if st.session_state.get("quick_win_active") and check_keyword_analysis_availability(plan_settings):
        st.divider()
        st.markdown("### ⚡ Quick Win Full Analysis")
        
        selected_keyword = st.session_state.get("selected_keyword")
        if selected_keyword:
            st.success(f"🎯 **Processing Quick Win:** {selected_keyword}")
            
            if st.button("🚀 Run Complete Analysis", type="primary"):
                with st.spinner("Running complete Quick Win analysis..."):
                    try:
                        # Import required functions
                        from ..utils.db_utils import safe_save_session, safe_save_brief, safe_save_serp, safe_save_suggestion
                        from ..core.services import generate_suggestions, fetch_serp_with_serpapi, fetch_serp_with_searchapi
                        import json
                        
                        # Step 1: Save session
                        session_id = safe_save_session(selected_keyword)
                        
                        # Step 2: Generate Brief
                        st.markdown("#### 📝 Generating Content Brief...")
                        brief_output, prompt, latency, usage = generate_brief_with_variant(
                            keyword=selected_keyword,
                            variant="A",
                            plan_settings=plan_settings
                        )
                        safe_save_brief(session_id, brief_output)
                        st.session_state.brief_output = brief_output
                        
                        # Step 3: Fetch SERP
                        st.markdown("#### 🔍 Fetching SERP Data...")
                        serp_provider = plan_settings.get("serp_provider", "serpapi")
                        if serp_provider == "serpapi":
                            serp_data = fetch_serp_with_serpapi(selected_keyword, plan_settings=plan_settings)
                        else:
                            serp_data = fetch_serp_with_searchapi(selected_keyword, plan_settings=plan_settings)
                        
                        safe_save_serp(session_id, json.dumps(serp_data))
                        st.session_state.serp_data = serp_data
                        
                        # Step 4: Generate AI Suggestions
                        st.markdown("#### 🤖 Generating AI Suggestions...")
                        suggestions = generate_suggestions(brief_output, serp_data, plan_settings)
                        for suggestion in suggestions:
                            safe_save_suggestion(session_id, suggestion)
                        
                        # Display Results
                        st.success("✅ **Quick Win Analysis Complete!**")
                        
                        # Show Brief
                        st.markdown("## 📋 Content Brief")
                        st.markdown(brief_output)
                        
                        # Show SERP Results
                        st.markdown("## 🔍 SERP Results")
                        if serp_data:
                            for i, result in enumerate(serp_data[:3], 1):
                                if isinstance(result, dict):
                                    st.markdown(f"**{i}. {result.get('title', 'No title')}**")
                                    st.markdown(f"🔗 {result.get('link', 'No link')}")
                                    st.markdown(f"📝 {result.get('snippet', 'No snippet')}")
                                    st.divider()
                        else:
                            st.info("No SERP data available")
                        
                        # Show AI Suggestions
                        st.markdown("## 💡 AI Content Suggestions")
                        for i, suggestion in enumerate(suggestions, 1):
                            st.markdown(f"{i}. {suggestion}")
                        
                        # Reset Quick Win state
                        st.session_state.quick_win_active = False
                        
                    except Exception as e:
                        st.error(f"Quick Win analysis failed: {str(e)}")
            
            # Option to cancel
            if st.button("❌ Cancel Quick Win"):
                st.session_state.quick_win_active = False
                st.rerun()
    
    # Navigation
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Back to Business Context"):
            state_manager.go_to_step(1)
    with col2:
        # Manual keyword entry option
        with st.expander("🔍 Search Google Keyword Planner Database"):
            search_term = st.text_input("Search for keywords:", placeholder="e.g., podcast, microphone, office chair")
            
            if search_term:
                from ..core.keywords import load_gkp_keywords, format_keyword_for_display
                plan_settings = st.session_state.get('plan_settings', {})
                
                try:
                    search_results = load_gkp_keywords(
                        topic=search_term,
                        max_results=5,  # Limit search results
                        plan_settings=plan_settings
                    )
                    
                    if search_results:
                        st.markdown("**Search Results:**")
                        for i, kw in enumerate(search_results):
                            formatted = format_keyword_for_display(kw)
                            col_search, col_use = st.columns([4, 1])
                            with col_search:
                                st.markdown(formatted)
                            with col_use:
                                if st.button("Use", key=f"search_{i}"):
                                    st.session_state.selected_keyword = kw.get('Keyword', '')
                                    st.session_state.selected_keyword_source = "GKP Search"
                                    state_manager.go_to_step(3)
                    else:
                        st.info("No keywords found. Try a different search term.")
                        
                except Exception as e:
                    st.error(f"Search error: {str(e)}")
            
            st.divider()
            manual_kw = st.text_input("Or enter a custom keyword:", placeholder="e.g., best marketing software")
            if manual_kw and st.button("Use this keyword"):
                st.session_state.selected_keyword = manual_kw
                st.session_state.selected_keyword_source = "Manual Entry"
                state_manager.go_to_step(3)


def render_step_3_brief():
    """Step 3: Content brief generation"""
    st.markdown("### 📋 Create Your Content Plan")
    
    selected_kw = st.session_state.get("selected_keyword")
    if not selected_kw:
        st.warning("No keyword selected. Please complete Step 2 first.")
        if st.button("← Back to Keywords"):
            state_manager.go_to_step(2)
        return
    
    # Enhanced keyword display with change option
    col1, col2 = st.columns([3, 1])
    with col1:
        st.success(f"🎯 **Target Keyword:** {selected_kw}")
        keyword_source = st.session_state.get("selected_keyword_source", "AI Generated")
        st.caption(f"📊 Source: {keyword_source}")
    with col2:
        if st.button("🔄 Change Keyword", help="Go back to select a different keyword"):
            state_manager.go_to_step(2)
    
    # Try to get GKP data for the selected keyword
    if keyword_source in ["Google Keyword Planner", "GKP Search"]:
        # Show enhanced keyword metrics
        try:
            from ..core.keywords import load_gkp_keywords
            plan_settings = st.session_state.get('plan_settings', {})
            
            gkp_data = load_gkp_keywords(selected_kw, max_results=1, plan_settings=plan_settings)
            if gkp_data:
                kw_data = gkp_data[0]
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Search Volume", f"{kw_data.get('Search Volume', 0):,}")
                with col2:
                    st.metric("Competition", f"{kw_data.get('Competition', 0):.0%}")
                with col3:
                    st.metric("Avg CPC", f"${kw_data.get('CPC', 0):.2f}")
                    
        except Exception as e:
            st.caption("Unable to load keyword metrics")
    
    # Brief format selection (improved clarity)
    brief_format = st.radio(
        "Choose your brief format:",
        ["📋 Executive Summary", "📝 Detailed Guide"], 
        horizontal=True,
        help="Executive Summary = Key points & strategy overview | Detailed Guide = Step-by-step content instructions"
    )
    # Convert to internal variant (both are SEO-optimized)
    variant_letter = "A" if "Executive Summary" in brief_format else "B"
    
    st.caption("💡 Both formats help your content get found by the right people")
    
    # Show plan-specific model info
    plan_settings = st.session_state.get('plan_settings', {})
    model_name = plan_settings.get('gpt_model', 'gpt-4o-mini')
    
    if model_name == "gpt-3.5-turbo":
        st.info("🆓 Using GPT-3.5-turbo for content generation (free tier)")
    elif model_name == "gpt-4":
        st.success("💎 Using GPT-4 for content generation (premium)")
    else:
        st.info(f"🤖 Using {model_name} for content generation")
    
    # Always show generate button with current state
    has_existing_brief = bool(st.session_state.get("brief_output"))
    button_text = "🔄 Regenerate Brief" if has_existing_brief else "🚀 Generate Content Brief"
    
    if st.button(button_text, type="primary"):
        with st.spinner("Generating content brief..."):
            try:
                brief_output, prompt, latency, usage = generate_brief_with_variant(
                    keyword=selected_kw,
                    variant=variant_letter,
                    plan_settings=st.session_state.get('plan_settings', {})
                )
                st.session_state.brief_output = brief_output
                st.session_state.brief_variant = variant_letter
                st.success("✅ Content brief generated successfully!")
                
                # Refresh page to show the generated brief
                st.rerun()
                
            except Exception as e:
                st.error(f"Error generating brief: {str(e)}")
    
    if not has_existing_brief:
        st.info("👀 **Next:** Get your content plan → See what competitors are doing → Get your complete strategy")
    
    # Show generated brief if available
    if st.session_state.get("brief_output"):
        st.divider()
        st.markdown("### 📋 Your Content Brief")
        st.info(f"Generated using Variant {st.session_state.get('brief_variant', 'A')}")
        
        # Display the brief content directly (not in expander)
        st.markdown(st.session_state.brief_output)
        
        st.divider()
        
        # Action buttons
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("← Back to Keywords"):
                state_manager.go_to_step(2)
        with col2:
            # Download brief button
            st.download_button(
                "📄 Download Brief",
                data=st.session_state.brief_output,
                file_name=f"brief_{selected_kw.replace(' ', '_')}.md",
                mime="text/markdown",
                use_container_width=True
            )
        with col3:
            if st.button("Continue to Competition Analysis →", type="primary"):
                state_manager.go_to_step(4)
    else:
        # Navigation
        col1, col2 = st.columns(2)
        with col1:
            if st.button("← Back to Keywords"):
                state_manager.go_to_step(2)
        with col2:
            st.caption("Generate a brief to continue")


def render_step_4_serp():
    """Step 4: SERP Analysis"""
    st.markdown("### 🔍 Step 4: Competition Analysis")
    
    selected_kw = st.session_state.get("selected_keyword")
    if not selected_kw:
        st.warning("No keyword selected. Please complete previous steps.")
        if st.button("← Back to Brief"):
            state_manager.go_to_step(3)
        return
    
    # Enhanced keyword display with change option
    col1, col2 = st.columns([3, 1])
    with col1:
        st.success(f"🎯 **Analyzing competition for:** {selected_kw}")
        # Show plan-specific SERP provider info
        plan_settings = st.session_state.get('plan_settings', {})
        serp_provider = plan_settings.get('serp_provider', 'serpapi')
        
        if serp_provider == "searchapi":
            st.caption(f"🆓 SearchAPI.io - analyzing up to {plan_settings.get('serp_results_limit', 5)} results")
        else:
            st.caption(f"💎 SerpAPI - analyzing up to {plan_settings.get('serp_results_limit', 20)} results")
    with col2:
        if st.button("🔄 Change Keyword", help="Go back to select a different keyword"):
            state_manager.go_to_step(2)
    
    # Always show analyze button with state awareness
    has_serp_data = bool(st.session_state.get("serp_data"))
    button_text = "🔄 Re-analyze Competition" if has_serp_data else "🔍 Analyze Competition"
    
    if st.button(button_text, type="primary"):
        with st.spinner("Analyzing search results..."):
            try:
                serp_data = fetch_serp_snapshot(
                    selected_kw, 
                    plan_settings=st.session_state.get('plan_settings', {})
                )
                st.session_state.serp_data = serp_data
                st.success("✅ Competition analysis completed!")
                
                # Refresh page to show the analysis results
                st.rerun()
                
            except Exception as e:
                st.error(f"Error analyzing competition: {str(e)}")
    
    if not has_serp_data:
        st.info("👀 **Next:** Analyze search results → Get competitor insights → Generate final strategy with actionable recommendations")
    
    # Show SERP data if available
    serp_data = st.session_state.get("serp_data", [])
    if serp_data:
        st.divider()
        st.markdown("#### 🏆 Top Competitors")
        st.caption("💡 Use this data to identify content gaps and opportunities for your content")
        
        for i, result in enumerate(serp_data[:5], 1):
            with st.expander(f"{i}. {result.get('title', 'No title')[:60]}..."):
                st.write(f"**URL:** {result.get('url', 'N/A')}")
                st.write(f"**Snippet:** {result.get('snippet', 'N/A')}")
        
        # Always show navigation options
        col1, col2 = st.columns(2)
        with col1:
            if st.button("← Back to Brief"):
                state_manager.go_to_step(3)
        with col2:
            if st.button("Get Final Strategy →", type="primary"):
                state_manager.go_to_step(5)
                
        st.info("👀 **Next:** Review your complete content strategy with actionable recommendations and export options")
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


# NEW WORKFLOW RENDERERS

def render_content_strategy_workflow():
    """Content Strategy workflow - Business context to strategy"""
    # Render main header
    workflow_info = ("content_strategy", "📝", "Content Strategy", "Business-focused content planning")
    render_main_header(workflow_info)
    
    # Workflow description
    st.info("🎯 Create a comprehensive content strategy based on your business goals. This workflow generates a complete strategic framework including content pillars, distribution strategy, and success metrics.")
    
    # Business context input
    col1, col2 = st.columns(2)
    with col1:
        business_desc = st.text_area(
            "Business Description:",
            value=st.session_state.get("strategy_business", ""),
            height=120,
            placeholder="Describe your business, products, and services..."
        )
    with col2:
        target_audience = st.text_input(
            "Target Audience:",
            value=st.session_state.get("strategy_audience", ""),
            placeholder="e.g., Small business owners, Tech professionals"
        )
        goals = st.multiselect(
            "Content Goals:",
            ["Drive Traffic", "Generate Leads", "Build Authority", "Educate", "Convert Sales"],
            default=st.session_state.get("strategy_goals", ["Drive Traffic"])
        )
    
    # Save inputs
    st.session_state.strategy_business = business_desc
    st.session_state.strategy_audience = target_audience
    st.session_state.strategy_goals = goals
    
    if business_desc and target_audience:
        if st.button("🚀 Generate Content Strategy", type="primary"):
            with st.spinner("Creating your content strategy..."):
                strategy = generate_content_strategy(business_desc, target_audience, goals)
                st.session_state.generated_strategy = strategy
                st.rerun()
        
        # Show generated strategy
        if st.session_state.get("generated_strategy"):
            st.divider()
            st.markdown("### 📋 Your Content Strategy")
            st.markdown(st.session_state.generated_strategy)
            
            # Download button
            st.download_button(
                "📥 Download Strategy",
                data=st.session_state.generated_strategy,
                file_name=f"content_strategy_{datetime.now().strftime('%Y%m%d')}.md",
                mime="text/markdown"
            )


def render_content_outline_workflow():
    """Content Outline workflow - Topic to detailed outline"""
    # Render main header
    workflow_info = ("content_outline", "📋", "Content Outline", "Detailed article outlines")
    render_main_header(workflow_info)
    
    # Workflow description
    st.info("📝 Create detailed, SEO-optimized content outlines. Perfect for writers, this tool generates comprehensive structures with sections, SEO considerations, and content guidelines.")
    
    # Topic input
    col1, col2 = st.columns(2)
    with col1:
        topic = st.text_input(
            "Content Topic:",
            value=st.session_state.get("outline_topic", ""),
            placeholder="e.g., Complete Guide to Email Marketing"
        )
        content_type = st.selectbox(
            "Content Type:",
            ["Blog Post", "Landing Page", "Guide", "Tutorial", "Case Study", "White Paper"],
            index=0
        )
    with col2:
        target_length = st.selectbox(
            "Target Length:",
            ["Short (500-1000 words)", "Medium (1000-2500 words)", "Long (2500+ words)"],
            index=1
        )
        audience_level = st.selectbox(
            "Audience Level:",
            ["Beginner", "Intermediate", "Advanced", "Mixed"],
            index=0
        )
    
    # Save inputs
    st.session_state.outline_topic = topic
    st.session_state.outline_content_type = content_type
    st.session_state.outline_length = target_length
    st.session_state.outline_audience = audience_level
    
    if topic:
        if st.button("📋 Generate Outline", type="primary"):
            with st.spinner("Creating detailed outline..."):
                outline = generate_content_outline(topic, content_type, target_length, audience_level)
                st.session_state.generated_outline = outline
                st.rerun()
        
        # Show generated outline
        if st.session_state.get("generated_outline"):
            st.divider()
            st.markdown("### 📄 Your Content Outline")
            st.markdown(st.session_state.generated_outline)
            
            # Download button
            st.download_button(
                "📥 Download Outline",
                data=st.session_state.generated_outline,
                file_name=f"outline_{topic.replace(' ', '_')}.md",
                mime="text/markdown"
            )


def render_content_ideas_workflow():
    """Content Ideas workflow - Niche to creative ideas"""
    # Render main header
    workflow_info = ("content_ideas", "💡", "Content Ideas", "Creative content brainstorming")
    render_main_header(workflow_info)
    
    # Workflow description
    st.info("🎨 Generate creative content ideas for your niche. Get inspiration for blog posts, social media, videos, and more with tailored suggestions for your audience.")
    
    # Input section
    col1, col2 = st.columns(2)
    with col1:
        niche = st.text_input(
            "Niche/Industry:",
            value=st.session_state.get("ideas_niche", ""),
            placeholder="e.g., Digital Marketing, Fitness, Finance"
        )
        audience = st.text_input(
            "Target Audience:",
            value=st.session_state.get("ideas_audience", ""),
            placeholder="e.g., Small business owners"
        )
    with col2:
        content_formats = st.multiselect(
            "Content Formats:",
            ["Blog Posts", "Social Media", "Videos", "Newsletters", "Podcasts", "Infographics"],
            default=["Blog Posts"]
        )
        idea_count = st.slider("Number of Ideas:", 5, 50, 20)
    
    # Save inputs
    st.session_state.ideas_niche = niche
    st.session_state.ideas_audience = audience
    st.session_state.ideas_formats = content_formats
    
    if niche:
        if st.button("💡 Generate Ideas", type="primary"):
            with st.spinner("Generating creative content ideas..."):
                ideas = generate_content_ideas(niche, audience, content_formats, idea_count)
                st.session_state.generated_ideas = ideas
                st.rerun()
        
        # Show generated ideas
        if st.session_state.get("generated_ideas"):
            st.divider()
            st.markdown("### 🎯 Your Content Ideas")
            st.markdown(st.session_state.generated_ideas)
            
            # Download button
            st.download_button(
                "📥 Download Ideas",
                data=st.session_state.generated_ideas,
                file_name=f"content_ideas_{niche.replace(' ', '_')}.md",
                mime="text/markdown"
            )


def render_quick_brief_workflow():
    """Quick Brief workflow - Keyword to instant brief"""
    # Render main header
    workflow_info = ("quick_brief", "🎯", "Quick Brief", "Fast content brief generation")
    render_main_header(workflow_info)
    
    # Workflow description
    st.info("⚡ Generate content briefs instantly from keywords. Perfect for quick content planning with optional competition analysis integration.")
    
    # Keyword input
    col1, col2 = st.columns(2)
    with col1:
        keyword = st.text_input(
            "Target Keyword:",
            value=st.session_state.get("quick_keyword", ""),
            placeholder="e.g., best project management software"
        )
        brief_depth = st.radio(
            "Content Depth:",
            ["📝 Essential Brief", "📚 Comprehensive Guide"],
            horizontal=True
        )
    with col2:
        word_count = st.selectbox(
            "Target Word Count:",
            ["500-1000", "1000-2000", "2000-3000", "3000+"],
            index=1
        )
        tone = st.selectbox(
            "Content Tone:",
            ["Professional", "Conversational", "Expert", "Friendly"],
            index=1
        )
    
    # Save inputs
    st.session_state.quick_keyword = keyword
    st.session_state.quick_depth = brief_depth
    st.session_state.quick_word_count = word_count
    st.session_state.quick_tone = tone
    
    if keyword:
        if st.button("⚡ Generate Quick Brief", type="primary"):
            with st.spinner("Generating content brief..."):
                try:
                    variant = "A" if "Essential Brief" in brief_depth else "B"
                    brief_output, prompt, latency, usage = generate_brief_with_variant(
                        keyword=keyword,
                        variant=variant,
                        plan_settings=st.session_state.get('plan_settings', {})
                    )
                    st.session_state.quick_brief_output = brief_output
                    st.rerun()
                except Exception as e:
                    st.error(f"Error generating brief: {str(e)}")
        
        # Show generated brief
        if st.session_state.get("quick_brief_output"):
            st.divider()
            st.markdown("### 📋 Your Quick Brief")
            st.markdown(st.session_state.quick_brief_output)
            
            # Action buttons
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    "📥 Download Brief",
                    data=st.session_state.quick_brief_output,
                    file_name=f"brief_{keyword.replace(' ', '_')}.md",
                    mime="text/markdown",
                    use_container_width=True
                )
            with col2:
                if st.button("🔍 Analyze Competition", use_container_width=True):
                    # Switch to full keyword research workflow with this keyword
                    st.session_state.selected_workflow = "keyword_research"
                    st.session_state.selected_keyword = keyword
                    st.session_state.brief_output = st.session_state.quick_brief_output
                    st.session_state.ux_step = 4  # Go to SERP analysis
                    st.rerun()


# Helper functions for new workflows
def generate_content_strategy(business_desc: str, audience: str, goals: list) -> str:
    """Generate comprehensive content strategy"""
    goals_str = ", ".join(goals).lower()
    
    return f"""# Content Strategy

## Business Overview
**Business:** {business_desc}
**Target Audience:** {audience}
**Primary Goals:** {goals_str}

## Content Strategy Framework

### 1. Content Pillars (40-30-20-10 Rule)
- **Educational Content (40%)**: How-to guides, tutorials, best practices
- **Community Content (30%)**: User stories, Q&A, discussions
- **Product/Service Content (20%)**: Features, benefits, case studies
- **Brand Content (10%)**: Behind-the-scenes, company culture

### 2. Content Calendar Structure
- **Weekly Themes**: Consistent topic focus
- **Monthly Campaigns**: Deeper strategic initiatives  
- **Quarterly Reviews**: Performance analysis and strategy updates

### 3. Distribution Strategy
- **Primary Platform**: Website/Blog
- **Social Media**: LinkedIn, Twitter (for B2B) or Instagram, Facebook (for B2C)
- **Email Marketing**: Weekly newsletters with curated content
- **Community Engagement**: Industry forums and groups

### 4. Success Metrics
Based on your goals ({goals_str}):
- **Traffic Growth**: 25% increase month-over-month
- **Lead Generation**: Track form submissions and content downloads
- **Engagement**: Comments, shares, time on page
- **Authority Building**: Backlinks, mentions, thought leadership

### 5. Content Production Workflow
1. **Research Phase**: Keyword research, competitor analysis
2. **Planning Phase**: Editorial calendar, content brief creation
3. **Creation Phase**: Writing, design, multimedia production
4. **Review Phase**: Quality control, SEO optimization
5. **Publishing Phase**: Schedule and distribute across channels
6. **Analysis Phase**: Performance tracking and optimization

### 6. Recommended Content Types
- Long-form guides and tutorials
- Case studies featuring {audience}
- Industry trend analysis
- Tool and resource roundups
- FAQ compilations

Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""


def generate_content_outline(topic: str, content_type: str, length: str, audience: str) -> str:
    """Generate detailed content outline"""
    
    return f"""# Content Outline: {topic}

## Content Details
**Type:** {content_type}
**Target Length:** {length}
**Audience Level:** {audience}

## Title Options
1. {topic}
2. The Complete Guide to {topic}
3. {topic}: Everything You Need to Know

## Meta Description
Discover everything about {topic} in this comprehensive guide. Learn best practices, avoid common mistakes, and get actionable insights.

## Content Structure

### Introduction (10% of content)
- **Hook**: Start with a compelling statistic or question
- **Problem Statement**: What challenge does this solve?
- **Value Proposition**: What will readers gain?
- **Content Preview**: Brief overview of what's covered

### Main Content Sections (80% of content)

#### Section 1: Fundamentals
- Definition and key concepts
- Why this matters
- Common misconceptions

#### Section 2: Getting Started
- Prerequisites and requirements
- Step-by-step initial setup
- Best practices for beginners

#### Section 3: Advanced Techniques
- Pro tips and strategies
- Tools and resources
- Optimization techniques

#### Section 4: Common Challenges
- Frequent mistakes to avoid
- Troubleshooting guide
- Solutions and workarounds

#### Section 5: Real-World Applications
- Case studies and examples
- Success stories
- Practical implementation

### Conclusion (10% of content)
- **Key Takeaways**: Main points summary
- **Next Steps**: What readers should do next
- **Call-to-Action**: Encourage engagement or conversion

## Additional Elements
- **Infographics**: Visual representations of key data
- **Checklists**: Actionable takeaway lists
- **Resource Links**: External tools and references
- **FAQ Section**: Address common questions
- **Related Content**: Internal linking opportunities

## SEO Considerations
- **Primary Keyword**: {topic}
- **Secondary Keywords**: Related terms and variations
- **Internal Links**: Link to relevant existing content
- **External Links**: Cite authoritative sources
- **Image Alt Text**: Optimize for accessibility and SEO

Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""


def generate_content_ideas(niche: str, audience: str, formats: list, count: int) -> str:
    """Generate creative content ideas"""
    
    ideas_sections = []
    
    # Blog post ideas
    blog_ideas = [
        f"Ultimate Guide to {niche} for {audience}",
        f"10 Common {niche} Mistakes {audience} Make",
        f"Case Study: How [Company] Achieved Success with {niche}",
        f"{niche} Tools Every {audience.rstrip('s')} Needs",
        f"Future of {niche}: Trends to Watch in 2024",
        f"{niche} on a Budget: Cost-Effective Strategies",
        f"Beginner's Guide to {niche}",
        f"Advanced {niche} Strategies for {audience}",
        f"{niche} Myths Debunked",
        f"How to Choose the Right {niche} Solution"
    ]
    
    # Social media ideas
    social_ideas = [
        f"Quick {niche} tips (carousel post)",
        f"Behind-the-scenes of {niche} process",
        f"{niche} before/after comparisons",
        f"Poll: What's your biggest {niche} challenge?",
        f"Quote graphics about {niche}",
        f"User-generated content featuring {niche}",
        f"Live Q&A about {niche}",
        f"{niche} tool recommendations"
    ]
    
    content_ideas = f"""# Content Ideas for {niche}

## Target Audience: {audience}
## Requested Formats: {', '.join(formats)}
## Generated Ideas: {count}

"""
    
    if "Blog Posts" in formats:
        content_ideas += f"""
### 📝 Blog Post Ideas
{chr(10).join(f"{i+1}. {idea}" for i, idea in enumerate(blog_ideas[:min(count//2, 10)]))}
"""
    
    if "Social Media" in formats:
        content_ideas += f"""
### 📱 Social Media Content Ideas
{chr(10).join(f"{i+1}. {idea}" for i, idea in enumerate(social_ideas[:min(count//3, 8)]))}
"""
    
    if "Videos" in formats:
        content_ideas += f"""
### 🎥 Video Content Ideas
1. {niche} Tutorial Series
2. Expert Interview about {niche}
3. {niche} Tool Reviews
4. Day in the Life of {audience}
5. {niche} Myths vs Reality
6. Quick {niche} Tips (60 seconds)
7. {niche} Case Study Walkthrough
8. Live {niche} Workshop
"""
    
    content_ideas += f"""
### 🎯 Content Calendar Suggestions

**Week 1**: Educational content (how-to guides)
**Week 2**: Community content (case studies, user stories)
**Week 3**: Product/tool content (reviews, comparisons)
**Week 4**: Trend/industry content (news, predictions)

### 📊 Content Performance Tracking
- Engagement rates (likes, shares, comments)
- Click-through rates to your website
- Lead generation from content
- Brand awareness metrics

Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""
    
    return content_ideas