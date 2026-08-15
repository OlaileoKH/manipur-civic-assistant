import httpx
import json
import tools
import datetime
import asyncio

async def run_agent_turn_async(messages_log: list):
    """Asynchronous agent turn routing with embedded temporal injection."""

    url = "http://localhost:11434/api/chat"
    
    # 1. GENERATE AND INJECT SYSTEM PROMPT FIRST
    current_date = datetime.datetime.now().strftime("%Y-%m-%d")
    system_prompt = {
        "role": "system",
        "content": (
            f"Today's date is {current_date}. You have tools: 'query_local_rag_vault' and 'search_web_internet'. "
            f"CRITICAL RULE: Any question asking for schedules, numbers, or information regarding specific local areas, neighborhoods, or streets in Manipur (such as Uripok, Khongman, Lamphel, etc.) MUST use 'query_local_rag_vault' first to check user-uploaded data. Only use 'search_web_internet' for broad public news, statewide policies, or national figures."
        )
    }



    
    # Safely insert or verify system context without duplicating on subsequent loops
    if not messages_log or messages_log[0].get("role") != "system":
        messages_log.insert(0, system_prompt)


    payload = {
        "model": "qwen2.5:7b-instruct",
        "messages": messages_log,
        "stream": False,
        "tools": tools.super_tool_registry,
        "options": {"temperature": 0.0}
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            response_data = response.json()
        except Exception as e:
            return f"Ollama Connection Error: {e}", None, messages_log

    msg = response_data.get("message", {})
    tool_calls = msg.get("tool_calls")

    if tool_calls:
        calls_list = tool_calls if isinstance(tool_calls, list) else [tool_calls]
        used_tool_names = []
        messages_log.append(msg)

        for call in calls_list:
            tool_name = call.get("function", {}).get("name") if "function" in call else call.get("name")
            tool_args = call.get("function", {}).get("arguments") if "function" in call else call.get("arguments")
            
            if isinstance(tool_args, str):
                try: tool_args = json.loads(tool_args)
                except: tool_args = {"query": tool_args}
            if not isinstance(tool_args, dict): tool_args = {}

            if tool_name == "query_local_rag_vault":
                output = tools.query_local_rag_vault(tool_args.get("query", ""))
            elif tool_name == "search_web_internet":
                output = tools.search_web_internet(tool_args.get("query", ""))
            elif tool_name == "execute_math_operation":
                raw_a = tool_args.get("a", 0)
                raw_b = tool_args.get("b", 0.0)
                
                # Protect against the model passing date strings or text into numbers
                try:
                    val_a = float(raw_a)
                except (ValueError, TypeError):
                    val_a = 0.0
                    
                try:
                    val_b = float(raw_b)
                except (ValueError, TypeError):
                    val_b = 0.0
                    
                output = tools.execute_math_operation(
                    operation=tool_args.get("operation", "add"),
                    a=val_a,
                    b=val_b
                )

            else:
                output = f"Tool '{tool_name}' not found."

            used_tool_names.append(tool_name)
            messages_log.append({"role": "tool", "name": tool_name, "content": output})

        final_payload = {
            "model": "qwen2.5:7b-instruct",
            "messages": messages_log,
            "stream": False,
            "options": {"temperature": 0.0}
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                final_resp = await client.post(url, json=final_payload)
                final_resp.raise_for_status()
                final_msg = final_resp.json().get("message", {})
                return final_msg.get("content", ""), ", ".join(used_tool_names), messages_log
            except Exception as e:
                return f"Synthesis error: {e}", ", ".join(used_tool_names), messages_log
    else:
        return msg.get("content", ""), None, messages_log
