import os
from string import Template
import importlib.util

class TemplateParser:
    def __init__(self, language: str = None, default_language='en'):
        self.current_path = os.path.dirname(os.path.abspath(__file__))
        self.default_language = default_language
        self.language = None
        self.set_language(language)

    def set_language(self, language: str):
        """Set the current language, fallback to default if not found"""
        if language:
            lang_path = os.path.join(self.current_path, "locales", language)
            if os.path.exists(lang_path):
                self.language = language
                return
        self.language = self.default_language

    def get_prompt(self, key: str, vars: dict = {}):
        """
        Fetch a prompt (parse or response) from the current language.
        Falls back to default language if not found.
        """
        group_path = os.path.join(self.current_path, "locales", self.language, "prompt.py")
        target_language = self.language

        if not os.path.exists(group_path):
            group_path = os.path.join(self.current_path, "locales", self.default_language, "prompt.py")
            target_language = self.default_language

        if not os.path.exists(group_path):
            return None

        # Load module dynamically
        spec = importlib.util.spec_from_file_location(f"{target_language}.prompts", group_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        if not hasattr(module, key):
            return None

        template: Template = getattr(module, key)
        return template.substitute(vars) if vars else template.template
