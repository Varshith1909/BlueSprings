import os
import textwrap
import dotenv
import google.generativeai as genai
from termcolor import colored
import time
from calculator_tool import parse_and_calculate, is_math_question, is_multi_step, CalculatorError

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
                for i in range(20):
                    print(f"\b{spinner[i % 4]}", end='', flush=True)
                    time.sleep(0.25)

                if is_multi_step(question):
                    print("\b" + colored("\nSorry, I can't answer multi-part questions (e.g., calculation and general knowledge) in one go.", 'red'))
                    continue
                elif is_math_question(question):
                    try:
                        answer = parse_and_calculate(question)
                        print("\b" + colored("\nCalculator:", 'cyan'))
                        print(f"The final answer is: {answer}")
                    except CalculatorError as ce:
                        print("\b" + colored(f"\nCalculator Error: {ce}", 'red'))
                    except Exception as ce:
                        print("\b" + colored(f"\nCalculator Error: {ce}", 'red'))
                else:
                    response = get_llm_response(question, model_name)
                    print("\b" + colored("\nAssistant:", 'green'))
                    print(response)
            except Exception as e:
                print("\b" + colored(f"\nError: {e}", 'red'))
                print("Please try again or check your connection.")
        except KeyboardInterrupt:
            print(colored("\nGoodbye!", 'magenta'))
            break

if __name__ == "__main__":
    main()