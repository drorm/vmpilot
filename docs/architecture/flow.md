

# Flow

- The app is started:
uvicorn main:app --port $PORT --host 0.0.0.0 --forwarded-allow-ips '*' --reload

- It detects pipelines/vmpilot.py and invokes it.
- The Pipeline class is instantiated.
- valves that correspond to fields in the UI are handled
- pipe is called with: (user_message: str, model_id: str, messages: List[dict], body: dict) 
- It collects the necessary data and then calls the `agent.process_messages` method

          process_messages(
              model=self.valves.model,
              provider=APIProvider(self.valves.provider.value),
              system_prompt_suffix=system_prompt_suffix,
              messages=formatted_messages,
              output_callback=output_callback,
              tool_output_callback=tool_callback,
              api_key=self._api_key,
              max_tokens=MAX_TOKENS,
              temperature=TEMPERATURE,
              disable_logging=body.get("disable_logging", False),
              recursion_limit=RECURSION_LIMIT,
          )
- agent.py does some house keeping and then calls `init_agent.create_agent` function
    agent = await create_agent(
        model, api_key, provider, system_prompt_suffix, temperature, max_tokens
    )
- It retrieves the history if any from unified_memory.get_conversation_state, 
- Creates a Chat object
- Creates an exchange object 
- and does a request.send_request to actually send the request to the model
    response, collected_tool_calls = await send_request(
        agent,
        chat,
        exchange,
        recursion_limit,
        formatted_messages,
        output_callback,
        tool_output_callback,
        usage,
    )
- it then handles the response: 
  - saving history
  - keep track of cost
