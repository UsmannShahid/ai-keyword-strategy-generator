"""
Prompt management for the AI Keyword Tool.
"""

import os
from typing import Dict, List, Optional, Tuple

class PromptManager:
    """Manages different prompt templates for keyword generation and A/B variants."""
    
    def __init__(self, prompts_dir: str = "data/prompts"):
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
        """Get list of available prompt names."""
        return list(self._prompts_cache.keys())
    
    def format_prompt_variant(self, base_name: str, variant: str, **kwargs) -> str:
        """Format a prompt variant with the given parameters."""
        prompt_key = f"{base_name}_{variant}"
        
        if prompt_key in self._prompts_cache:
            prompt_template = self._prompts_cache[prompt_key]
        else:
            # Fallback to base prompt or default
            prompt_template = self._prompts_cache.get(base_name, f"Generate content for: {kwargs}")
        
        # Simple string formatting
        try:
            return prompt_template.format(**kwargs)
        except:
            return prompt_template

# Global instance
prompt_manager = PromptManager()