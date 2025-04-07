from typing import Dict, List, Optional, Tuple, Union

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import ollama


class BaseModel:
    def __init__(self, path: str = "") -> None:
        self.path = path

    def chat(self, prompt: str, history: List[dict]):
        pass

    def load_model(self):
        pass


class OllamaModel(BaseModel):
    def __init__(self, model: str = "qwen2.5:3b") -> None:
        self.model = model

    def chat(self, prompt: str, history: List[dict], meta_instruction: str = ""):
        response = ollama.chat(
            model=self.model,
            messages=[
                {"role": "system", "content": meta_instruction},
                {"role": "user", "content": prompt},
            ],
        )
        return response.message.content, history

    def load_model(self):
        pass


class InternLM2Chat(BaseModel):
    def __init__(self, path: str = "") -> None:
        super().__init__(path)
        self.load_model()

    def load_model(self):
        print("================ Loading model ================")
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.path, trust_remote_code=True
        )
        # self.model = AutoModelForCausalLM.from_pretrained(self.path, torch_dtype=torch.float16, trust_remote_code=True).cuda().eval()
        self.model = (
            AutoModelForCausalLM.from_pretrained(
                # self.path, torch_dtype=torch.float32, trust_remote_code=True,
                self.path,
                torch_dtype=torch.float16,
                trust_remote_code=True,
            )
            .to(
                torch.device("mps") if torch.mps.is_available() else torch.device("cpu")
            )
            .eval()
        )
        print("================ Model loaded ================")

    def chat(self, prompt: str, history: List[dict], meta_instruction: str = "") -> str:
        response, history = self.model.chat(
            self.tokenizer,
            prompt,
            history,
            temperature=0.1,
            meta_instruction=meta_instruction,
        )
        return response, history


# if __name__ == '__main__':
#     model = InternLM2Chat('/root/share/model_repos/internlm2-chat-7b')
#     print(model.chat('Hello', []))

# if __name__ == '__main__':
#     model = OllamaModel('qwen2.5:1.5b')
#     print(model.chat('Hello', []))
