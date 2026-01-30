"""
Prompt Builder Module

This module provides a flexible system for building GPT prompts dynamically
from modular sections. Prompts are assembled based on context and mode requirements.
"""

import os
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class PromptSection:
    """
    Represents a single section of a prompt with template variable support.
    
    Sections can include template variables in {variable_name} format that
    are replaced during rendering.
    """
    
    def __init__(self, name: str, content: str, required_context: Optional[List[str]] = None):
        """
        Initialize a prompt section.
        
        Args:
            name: Unique identifier for the section (e.g., 'base/system_role')
            content: The text content of the section
            required_context: Optional list of required context variable names
        """
        self.name = name
        self.content = content
        self.required_context = required_context or []
    
    def render(self, context: Dict) -> str:
        """
        Render the section with context variables.
        
        Args:
            context: Dictionary of variable names to values
            
        Returns:
            Rendered section with variables substituted
            
        Raises:
            ValueError: If required context variables are missing
        """
        # Check for required context
        missing = [var for var in self.required_context if var not in context]
        if missing:
            logger.warning(f"Section '{self.name}' missing required context: {missing}")
        
        # Replace template variables
        rendered = self.content
        for key, value in context.items():
            placeholder = f"{{{key}}}"
            if placeholder in rendered:
                rendered = rendered.replace(placeholder, str(value))
        
        return rendered


class PromptBuilder:
    """
    Builds GPT prompts dynamically from modular sections.
    
    The builder loads sections from the prompt_sections directory and
    assembles them based on the requested section names and context.
    """
    
    def __init__(self, sections_dir: Optional[str] = None):
        """
        Initialize the prompt builder.
        
        Args:
            sections_dir: Path to prompt sections directory. If None, uses default location.
        """
        if sections_dir is None:
            # Default to core/prompt_sections relative to this file
            backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            sections_dir = os.path.join(backend_root, "core", "prompt_sections")
        
        self.sections_dir = sections_dir
        self.sections: Dict[str, PromptSection] = {}
        self._load_sections()
    
    def _load_sections(self):
        """
        Load all prompt sections from the sections directory.
        
        Sections are organized in subdirectories (base/, feedback/, etc.)
        and loaded with their relative path as the name (e.g., 'base/system_role').
        """
        if not os.path.exists(self.sections_dir):
            logger.warning(f"Prompt sections directory not found: {self.sections_dir}")
            return
        
        sections_loaded = 0
        
        # Walk through all subdirectories
        for root, dirs, files in os.walk(self.sections_dir):
            for filename in files:
                if filename.endswith('.txt'):
                    filepath = os.path.join(root, filename)
                    
                    # Create section name from relative path
                    relative_path = os.path.relpath(filepath, self.sections_dir)
                    section_name = relative_path.replace('.txt', '').replace(os.sep, '/')
                    
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # Extract required context from comments (optional)
                        required_context = self._extract_required_context(content)
                        
                        section = PromptSection(section_name, content, required_context)
                        self.sections[section_name] = section
                        sections_loaded += 1
                        
                    except Exception as e:
                        logger.error(f"Error loading section '{section_name}': {e}")
        
        logger.info(f"Loaded {sections_loaded} prompt sections from {self.sections_dir}")
    
    def _extract_required_context(self, content: str) -> List[str]:
        """
        Extract required context variables from section content.
        
        Looks for variables in {variable_name} format.
        
        Args:
            content: Section content
            
        Returns:
            List of variable names found in the content
        """
        import re
        # Find all {variable} patterns
        variables = re.findall(r'\{(\w+)\}', content)
        return list(set(variables))  # Remove duplicates
    
    def build_prompt(
        self,
        sections: List[str],
        context: Optional[Dict] = None,
        include_ssml: bool = True
    ) -> str:
        """
        Build a complete prompt from specified sections.
        
        Args:
            sections: List of section names to include (e.g., ['base/system_role', 'feedback/praise_criteria'])
            context: Dictionary of context variables for template substitution
            include_ssml: Whether to include SSML instructions (default: True)
            
        Returns:
            Complete assembled prompt with all sections and variables substituted
            
        Raises:
            ValueError: If a requested section is not found
        """
        if context is None:
            context = {}
        
        # Add SSML section if requested and not already in the list
        if include_ssml and 'ssml/ssml_minimal' not in sections:
            sections = sections + ['ssml/ssml_minimal']
        
        assembled_parts = []
        
        for section_name in sections:
            if section_name not in self.sections:
                logger.warning(f"Section '{section_name}' not found. Available: {list(self.sections.keys())}")
                continue
            
            section = self.sections[section_name]
            rendered = section.render(context)
            assembled_parts.append(rendered)
        
        # Join sections with double newline
        prompt = "\n\n".join(assembled_parts)
        
        logger.info(f"Built prompt with {len(sections)} sections ({len(prompt)} chars)")
        
        return prompt
    
    def get_available_sections(self) -> List[str]:
        """
        Get list of all available section names.
        
        Returns:
            List of section names
        """
        return list(self.sections.keys())
    
    def reload_sections(self):
        """
        Reload all sections from disk.
        
        Useful for development when sections are being edited.
        """
        self.sections.clear()
        self._load_sections()


# Convenience function for quick prompt building
def build_prompt(sections: List[str], context: Optional[Dict] = None, include_ssml: bool = True) -> str:
    """
    Convenience function to build a prompt without creating a PromptBuilder instance.
    
    Args:
        sections: List of section names to include
        context: Dictionary of context variables
        include_ssml: Whether to include SSML instructions
        
    Returns:
        Complete assembled prompt
    """
    builder = PromptBuilder()
    return builder.build_prompt(sections, context, include_ssml)
