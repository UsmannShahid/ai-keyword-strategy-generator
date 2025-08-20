# prompt_manager.py
import os
from typing import Dict, List, Optional, Tuple

class PromptManager:
    """Manages different prompt templates for keyword generation and A/B variants."""
    
    def __init__(self, prompts_dir: str = "prompts"):
        self.prompts_dir = prompts_dir
        self._prompts_cache: Dict[str, str] = {}
        self._load_prompts()
    
    def _load_prompts(self):
        """Load all prompt files from the prompts directory."""
        if not os.path.exists(self.prompts_dir):
            os.makedirs(self.prompts_dir)
            return
        
        for filename in os.listdir(self.prompts_dir):
            if filename.endswith('.txt'):
                prompt_name = filename[:-4]  # Remove .txt extension
                filepath = os.path.join(self.prompts_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        self._prompts_cache[prompt_name] = f.read().strip()
                except Exception as e:
                    print(f"Warning: Could not load prompt {filename}: {e}")
    
    def get_available_prompts(self) -> List[str]:
        """Get list of available prompt names (raw keys, e.g., 'content_brief_A')."""
        return list(self._prompts_cache.keys())

    # --- NEW: variant parsing helpers ---------------------------------
    @staticmethod
    def _split_base_and_variant(key: str) -> Tuple[str, Optional[str]]:
        """
        Split a key like 'content_brief_A' -> ('content_brief', 'A').
        If no variant suffix, returns (key, None).
        """
        if "_" in key:
            base, suffix = key.rsplit("_", 1)
            # Treat 1–3 char suffixes as variants, e.g., A, B, C, v1
            if 1 <= len(suffix) <= 3:
                return base, suffix
        return key, None

    def get_variants(self, base_name: str) -> List[str]:
        """List available variants for a base prompt (e.g., 'content_brief' -> ['A','B'])."""
        variants = []
        for key in self._prompts_cache.keys():
            base, variant = self._split_base_and_variant(key)
            if base == base_name and variant:
                variants.append(variant)
        return sorted(variants)

    def has_prompt_variant(self, base_name: str, variant: Optional[str]) -> bool:
        """Check if a base+variant exists."""
        if variant:
            return f"{base_name}_{variant}" in self._prompts_cache
        return base_name in self._prompts_cache
    # -------------------------------------------------------------------

    def get_prompt_display_names(self) -> Dict[str, str]:
        """
        Returns human-friendly labels for prompt templates.
        Maps internal keys to display names used in the UI.
        """
        return {
            "default_seo": "🎯 Balanced SEO Strategy",
            "competitive_analysis": "🔍 Competitive Analysis",
            "long_tail_focus": "🌱 Long-Tail Keywords (Low Volume, High Intent)",
            "trend_hunting": "📈 Trending Searches",
            "local_seo": "📍 Local SEO Focus",
            "buyer_intent": "💰 High Buyer Intent",
            "content_gaps": "🔍 Content Gap Analysis",
            "seasonal_trending": "🌟 Seasonal & Trending",
        }

    
    def get_prompt(self, prompt_name: str) -> str:
        """
        Get a specific prompt template by raw key (e.g., 'content_brief_A' or 'default_seo').
        """
        if prompt_name not in self._prompts_cache:
            raise ValueError(f"Prompt '{prompt_name}' not found. Available: {list(self._prompts_cache.keys())}")
        return self._prompts_cache[prompt_name]

    # --- NEW: variant-aware getter ------------------------------------
    def get_prompt_variant(self, base_name: str, variant: Optional[str] = None) -> str:
        """
        Get prompt by base + variant. If variant is None, tries exact base key.
        """
        key = f"{base_name}_{variant}" if variant else base_name
        return self.get_prompt(key)
    # -------------------------------------------------------------------
    
    def format_prompt(self, prompt_name: str, **kwargs) -> str:
        """Format a prompt with the given variables."""
        template = self.get_prompt(prompt_name)
        try:
            return template.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"Missing required variable {e} for prompt '{prompt_name}'")

    # --- NEW: variant-aware formatter ---------------------------------
    def format_prompt_variant(self, base_name: str, variant: Optional[str] = None, **kwargs) -> str:
        """
        Format a base+variant prompt with variables, e.g. ('content_brief','A', keyword='...').
        """
        template = self.get_prompt_variant(base_name, variant)
        try:
            return template.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"Missing required variable {e} for prompt '{base_name}_{variant or ''}'")
    # -------------------------------------------------------------------
    
    def reload_prompts(self):
        """Reload all prompts from disk (useful for development)."""
        self._prompts_cache.clear()
        self._load_prompts()

# Create a global instance
prompt_manager = PromptManager()
