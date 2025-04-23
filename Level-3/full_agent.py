import os
import textwrap
import dotenv
import google.generativeai as genai
from termcolor import colored
import time
import re
from calculator_tool import parse_and_calculate, is_math_question, CalculatorError
from translator_tool import translate_to_german, is_translation_request, extract_text_to_translate, TranslationError

conversation_memory = []

def configure_gemini():
    try:
        dotenv.load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("API key not found. Please set GEMINI_API_KEY in .env file or environment variables.")
        genai.configure(api_key=api_key)
        model_name = 'models/gemini-1.5-pro'
        model = genai.GenerativeModel(model_name)
        model.generate_content("Test connection", request_options={"timeout": 5})
        return model_name
    except Exception as e:
        print(colored(f"Configuration error: {e}", 'red'))
        return None

def get_llm_response(question, model_name):
    try:
        model = genai.GenerativeModel(model_name)
        system_prompt = textwrap.dedent("""
        You are a helpful AI assistant that answers questions with clear explanations.
        Rules:
        1. Think step-by-step
        2. Refuse calculations
        3. Structure answers clearly
        4. Do not answer complex questions
        5. Do not answer multiple questions
        """)
        response = model.generate_content(
            system_prompt + question,
            request_options={"timeout": 10}
        )
        if not response.text:
            raise ValueError("Received empty response from API")
        return response.text
    except Exception as e:
        raise Exception(f"API Error: {str(e)}")

def extract_calculation_segments(query):
    segments = []
    
    patterns = [
        # Addition patterns
        r'(?:add|sum|plus)\s+([\d.]+)\s+(?:and|to|with)\s+([\d.]+)',
        r'([\d.]+)\s*\+\s*([\d.]+)',
        
        # Subtraction patterns
        r'(?:subtract|minus)\s+([\d.]+)\s+(?:from)\s+([\d.]+)',
        r'(?:subtract|minus)\s+([\d.]+)\s+(?:and|to|with)\s+([\d.]+)',
        r'([\d.]+)\s*\-\s*([\d.]+)',
        
        # Multiplication patterns
        r'(?:multiply|times)\s+([\d.]+)\s+(?:and|by|with)\s+([\d.]+)',
        r'([\d.]+)\s*(?:\*|x|×)\s*([\d.]+)',
        
        # Division patterns
        r'(?:divide)\s+([\d.]+)\s+(?:by|with)\s+([\d.]+)',
        r'([\d.]+)\s*\/\s*([\d.]+)'
    ]
    
    all_matches = []
    for pattern in patterns:
        matches = re.finditer(pattern, query, re.IGNORECASE)
        for match in matches:
            all_matches.append((match.start(), match.group(0)))
    
    all_matches.sort(key=lambda x: x[0])
    
    for _, match_text in all_matches:
        segments.append(match_text)
    
    if not segments:
        potential_segments = re.split(r'(?<=\d)\s+and\s+(?=\d|add|subtract|multiply|divide)', query)
        segments = [seg.strip() for seg in potential_segments if is_math_question(seg)]
    
    if not segments and is_math_question(query):
        segments = [query]
    
    return segments

def identify_steps(question):
    steps = []
    
    explicit_parts = re.split(r',\s*|\s+and\s+then\s+|\s+then\s+', question)
    
    if len(explicit_parts) > 1:
        for part in explicit_parts:
            part = part.strip()
            if not part:
                continue
                
            if is_translation_request(part):
                text_to_translate = extract_text_to_translate(part)
                if text_to_translate:
                    steps.append(("translate", text_to_translate))
            elif is_math_question(part):
                calc_segments = extract_calculation_segments(part)
                for segment in calc_segments:
                    steps.append(("calculate", segment))
            else:
                steps.append(("llm", part))
    else:
        if is_translation_request(question):
            text_to_translate = extract_text_to_translate(question)
            if text_to_translate:
                steps.append(("translate", text_to_translate))

        if is_math_question(question):
            calc_segments = extract_calculation_segments(question)
            for segment in calc_segments:
                steps.append(("calculate", segment))

        if not steps:
            steps.append(("llm", question))
    
    return steps

def main():
    model_name = configure_gemini()
    if not model_name:
        return
    
    while True:
        try:
            question = input(colored("\nYou: ", 'blue'))
            if question.lower() in ['exit', 'quit', 'q']:
                print(colored("\nGoodbye!", 'magenta'))
                break
            if not question.strip():
                continue
                
            print(colored("\nThinking...", 'yellow'), end='', flush=True)
            
            try:
                spinner = ['|', '/', '-', '\\']
                for i in range(5):
                    print(f"\b{spinner[i % 4]}", end='', flush=True)
                    time.sleep(0.1)

                steps = identify_steps(question)
                
                for i, (step_type, step_content) in enumerate(steps):
                    if step_type == "translate":
                        try:
                            german_text = translate_to_german(step_content)
                            print("\b" + colored("\nTranslator:", 'cyan'))
                            print(f"'{step_content}' in German is: '{german_text}'")
                            
                            conversation_memory.append({
                                "query": f"Translate '{step_content}' to German", 
                                "response": f"'{step_content}' in German is: '{german_text}'",
                                "source": "Translator"
                            })
                        except TranslationError as te:
                            print("\b" + colored(f"\nTranslator Error: {te}", 'red'))
                    
                    elif step_type == "calculate":
                        try:
                            result = parse_and_calculate(step_content)
                            print("\b" + colored("\nCalculator:", 'cyan'))
                            print(f"The final answer is: {result}")
                            
                            conversation_memory.append({
                                "query": step_content, 
                                "response": f"The final answer is: {result}",
                                "source": "Calculator"
                            })
                        except CalculatorError as ce:
                            print("\b" + colored(f"\nCalculator Error: {ce}", 'red'))
                    
                    else:  # LLM
                        try:
                            llm_response = get_llm_response(step_content, model_name)
                            print("\b" + colored("\nAssistant:", 'green'))
                            print(llm_response)

                            conversation_memory.append({
                                "query": step_content, 
                                "response": llm_response,
                                "source": "Assistant"
                            })
                        except Exception as e:
                            print("\b" + colored(f"\nAssistant Error: {e}", 'red'))
                    
                    if i < len(steps) - 1:
                        print(colored("\n" + "-" * 40, 'yellow'))
                    
            except Exception as e:
                print("\b" + colored(f"\nError: {e}", 'red'))
                print("Please try again or check your connection.")
                
        except KeyboardInterrupt:
            print(colored("\nGoodbye!", 'magenta'))
            break

if __name__ == "__main__":
    main()