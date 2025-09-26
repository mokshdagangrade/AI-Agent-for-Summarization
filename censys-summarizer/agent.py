import json
import re
from actions import summarize_host_action, qa_action, evaluate_output_action
from prompts import SYSTEM_PROMPT
from utils import client
from typing import Optional, Dict

# Map action names to Python functions
AVAILABLE_ACTIONS = {
    "summarize_host_action": summarize_host_action,
    "qa_action": qa_action,
    "evaluate_output_action": evaluate_output_action
}

# Global message to store history of conversation
MESSAGES = [{"role": "system", "content": SYSTEM_PROMPT}]

import re

def extract_final_answer(agent_output_content: str):
    patterns = [
        r"Final Answer:\s*(?:```(?:markdown)?\s*)?(.*?)(?:```)?\s*$", 
        r"Answer:\s*(?:```(?:markdown)?\s*)?(.*?)(?:```)?\s*$"       
    ]
    for pattern in patterns:
        match = re.search(pattern, agent_output_content, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return agent_output_content 


def extract_json_action(text: str) -> Optional[Dict]:
    
    try:
        cleaned = re.sub(r"```json|```", "", text, flags=re.IGNORECASE)

        brace_level = 0
        json_start = None
        for i, char in enumerate(cleaned):
            if char == '{':
                if brace_level == 0:
                    json_start = i
                brace_level += 1
            elif char == '}':
                brace_level -= 1
                if brace_level == 0 and json_start is not None:
                    json_str = cleaned[json_start:i+1]
                    return json.loads(json_str)
        return None
    except json.JSONDecodeError:
        return None
    except Exception:
        return None

# The main agent function
def run_agent(user_question: str, max_turns=3, model="mistralai/Mistral-7B-Instruct-v0.2:featherless-ai"):
    global MESSAGES

    turn = 0

    MESSAGES.append({"role": "user", "content": user_question})
    
    for _ in range(max_turns):
        turn += 1
        print(f"\n--- Turn {turn} ---")

        response = client.chat.completions.create(
            model=model,
            messages=MESSAGES
        )
        agent_output = response.choices[0].message
        print(agent_output.content)

        json_action = extract_json_action(agent_output.content)
        print("Extracted action:", json_action)

        if json_action:
            function_name = list(json_action.keys())[0]
            params = json_action[function_name]

            if function_name in AVAILABLE_ACTIONS:
                result = AVAILABLE_ACTIONS[function_name](**params)
                print(f"Action result: {result}")

                MESSAGES.append({"role": "user", "content": f"Action_Response: {json.dumps(result)}"})
            else:
                MESSAGES.append({"role": "user", "content": f"Action_Response: Unknown function {function_name}"})
        else:
            pass

        eval_result = evaluate_output_action(agent_output.content)
        print(f"Evaluation result: {eval_result}")
        MESSAGES.append({"role": "user", "content": f"Evaluation_Response: {json.dumps(eval_result)}"})

        if not json_action:
            break

    return agent_output.content
