from typing import Dict, List, Optional, Tuple, Union
import json5

from tinyAgent.LLM import InternLM2Chat, OllamaModel
from tinyAgent.tool import Tools


TOOL_DESC = """{name_for_model}: Call this tool to interact with the {name_for_human} API. What is the {name_for_human} API useful for? {description_for_model} Parameters: {parameters} Format the arguments as a JSON object."""
REACT_PROMPT = """Answer the following questions as best you can. You have access to the following tools:

{tool_descs}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can be repeated zero or more times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!
"""


class Agent:
    def __init__(self, path: str = '') -> None:
        self.path = path
        self.tool = Tools()
        self.system_prompt = self.build_system_input()
        # self.model = InternLM2Chat(path)
        self.model = OllamaModel(path)

        self.max_retry = 5

        self.retry = 0

    def build_system_input(self):
        tool_descs, tool_names = [], []
        for tool in self.tool.toolConfig:
            tool_descs.append(TOOL_DESC.format(**tool))
            tool_names.append(tool['name_for_model'])
        tool_descs = '\n\n'.join(tool_descs)
        tool_names = ','.join(tool_names)
        sys_prompt = REACT_PROMPT.format(tool_descs=tool_descs, tool_names=tool_names)
        return sys_prompt
    
    def parse_latest_plugin_call(self, text):
        plugin_name, plugin_args = '', ''
        i = text.rfind('\nAction:')
        j = text.rfind('\nAction Input:')
        k = text.rfind('\nObservation:')
        if 0 <= i < j:  # If the text has `Action` and `Action input`,
            if k < j:  # but does not contain `Observation`,
                text = text.rstrip() + '\nObservation:'  # Add it back.
            k = text.rfind('\nObservation:')
            plugin_name = text[i + len('\nAction:') : j].strip()
            plugin_args = text[j + len('\nAction Input:') : k].strip()
            text = text[:k]
        return plugin_name, plugin_args, text
    
    def call_plugin(self, plugin_name, plugin_args):
        plugin_args = json5.loads(plugin_args)
        if plugin_name == 'google_search':
            return '\nObservation:' + self.tool.google_search(**plugin_args)
        elif plugin_name == 'bing_search':
            return '\nObservation:' + self.tool.bing_search(**plugin_args)

    def text_completion_old(self, text, history=[]):
        text = "\nQuestion:" + text
        response, his = self.model.chat(text, history, self.system_prompt)
        print(response)
        print(f"{'='*10} before call tools {'='*10}")
        plugin_name, plugin_args, response = self.parse_latest_plugin_call(response)
        print(f"plugin_name: {plugin_name}")
        if plugin_name:
            response += self.call_plugin(plugin_name, plugin_args)
        print(response)
        print(f"{'='*10} after call tools {'='*10}")
        response, his = self.model.chat(response, history, self.system_prompt)
        return response, his

    def text_completion_v1(self, text, history=[]):
        import os

        os.environ["TOKENIZERS_PARALLELISM"] = "true"

        text = "\nQuestion:" + text
        response, his = self.model.chat(text, history, self.system_prompt)
        print(f"{'='*10} before call tools start {'='*10}")
        print(response)
        history.append(response)
        print(f"history size: {len(history)}")
        print(f"{'='*10} before call tools end {'='*10}")
        plugin_name, plugin_args, response = self.parse_latest_plugin_call(
            response
        )
        print(f"plugin_name: {plugin_name}")
        if plugin_name:
            response += self.call_plugin(plugin_name, plugin_args)
        print(f"{'='*10} after call tools start {'='*10}")
        print(response)
        history.append(response)
        print(f"history size: {len(history)}")
        print(f"{'='*10} after call tools end {'='*10}")
        response, his = self.model.chat(
            response, history, self.system_prompt
        )
        print(f"{'='*10} after summary start {'='*10}")
        print(response)
        history.append(response)
        print(f"history size: {len(history)}")
        print(f"{'='*10} after summary end {'='*10}")
        return response, his
    
    def _handle(self, response: str, history=[]):
        if self.retry >= self.max_retry:
            return response, history
        self.retry += 1
        print(f"retry: {self.retry}")
        plugin_name, plugin_args, response = self.parse_latest_plugin_call(
            response
        )
        print(f"plugin_name: {plugin_name}")
        if plugin_name:
            response += self.call_plugin(plugin_name, plugin_args)

            print(f"{'='*10} after call tools start {'='*10}")
            print(response)
            history.append(response)
            print(f"history size: {len(history)}")
            print(f"{'='*10} after call tools end {'='*10}")
            response, his = self.model.chat(
                response, history, self.system_prompt
            )
            print(f"{'='*10} after summary start {'='*10}")
            print(response)
            history.append(response)
            print(f"history size: {len(history)}")
            print(f"{'='*10} after summary end {'='*10}")
            return response, history
        else:
            response, his = self.model.chat(
                response, history, self.system_prompt
            )
            print(f"{'='*10} after retry start {'='*10}")
            print(response)
            history.append(response)
            print(f"history size: {len(history)}")
            print(f"{'='*10} after retry end {'='*10}")
            return self._handle(response, history)
    
    def text_completion(self, text, history=[]):
        import os

        os.environ["TOKENIZERS_PARALLELISM"] = "true"

        text = "\nQuestion:" + text
        response, his = self.model.chat(text, history, self.system_prompt)
        print(f"{'='*10} before call tools start {'='*10}")
        print(response)
        history.append(response)
        print(f"history size: {len(history)}")
        print(f"{'='*10} before call tools end {'='*10}")

        self.retry = 0
        return self._handle(response, history)

if __name__ == '__main__':
    agent = Agent('/root/share/model_repos/internlm2-chat-7b')
    prompt = agent.build_system_input()
    print(prompt)