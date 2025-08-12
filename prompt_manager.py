# prompt_manager.py
import os
from typing import Dict, List

class PromptManager:
    """Manages different prompt templates for keyword generation."""
    
    def __init__(self, prompts_dir: str = "prompts"):
        self.prompts_dir = prompts_dir
        self._prompts_cache = {}
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
        """Get list of available prompt names."""
        return list(self._prompts_cache.keys())
    
    def get_prompt_display_names(self) -> Dict[str, str]:
        """Get mapping of prompt keys to display-friendly names."""
        display_names = {
            'default_seo': '🎯 Default SEO Strategy',
            'competitive_analysis': '🔍 Competitive Analysis',
        }
        
        # Add any other prompts with generic names
        for prompt_name in self._prompts_cache.keys():
            if prompt_name not in display_names:
                # Convert snake_case to Title Case
                display_name = prompt_name.replace('_', ' ').title()
                display_names[prompt_name] = f"📝 {display_name}"
        
        return display_names
    
    def get_prompt(self, prompt_name: str) -> str:
        """Get a specific prompt template."""
        if prompt_name not in self._prompts_cache:
            raise ValueError(f"Prompt '{prompt_name}' not found. Available: {list(self._prompts_cache.keys())}")
        return self._prompts_cache[prompt_name]
    
    def format_prompt(self, prompt_name: str, **kwargs) -> str:
        """Format a prompt with the given variables."""
        template = self.get_prompt(prompt_name)
        try:
            return template.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"Missing required variable {e} for prompt '{prompt_name}'")
    
    def reload_prompts(self):
        """Reload all prompts from disk (useful for development)."""
        self._prompts_cache.clear()
        self._load_prompts()

# Create a global instance
prompt_manager = PromptManager()
