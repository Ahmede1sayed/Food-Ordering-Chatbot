











from llm.LLMProviderFactory import load_prompts
from llm.LLMEnums import Language

# Load prompts based on default language (.env)
prompts = load_prompts()  

# OR force Arabic
# prompts = load_prompts(Language.AR)

user_query = "Hello, how are you?"
prompt_text = prompts.system_prompt.template + "\n" + prompts.query_prompt.substitute(query=user_query)

# Now send `prompt_text` to your LLM provider
# response = llm_provider.generate(prompt_text)
# print(response)
