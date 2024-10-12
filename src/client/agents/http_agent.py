import contextlib
import time
import warnings
import math
import requests
from urllib3.exceptions import InsecureRequestWarning

from src.typings import *
from src.utils import *
from src.utils.image_message import replace_image_url
from ..agent import AgentClient

old_merge_environment_settings = requests.Session.merge_environment_settings


@contextlib.contextmanager
def no_ssl_verification():
    opened_adapters = set()

    def merge_environment_settings(self, url, proxies, stream, verify, cert):
        # Verification happens only once per connection so we need to close
        # all the opened adapters once we're done. Otherwise, the effects of
        # verify=False persist beyond the end of this context manager.
        opened_adapters.add(self.get_adapter(url))

        settings = old_merge_environment_settings(self, url, proxies, stream, verify, cert)
        settings['verify'] = False

        return settings

    requests.Session.merge_environment_settings = merge_environment_settings

    try:
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', InsecureRequestWarning)
            yield
    finally:
        requests.Session.merge_environment_settings = old_merge_environment_settings

        for adapter in opened_adapters:
            try:
                adapter.close()
            except:
                pass


class Prompter:
    @staticmethod
    def get_prompter(prompter: Union[Dict[str, Any], None]):
        # check if prompter_name is a method and its variable
        if not prompter:
            return Prompter.default()
        assert isinstance(prompter, dict)
        prompter_name = prompter.get("name", None)
        prompter_args = prompter.get("args", {})
        if hasattr(Prompter, prompter_name) and callable(
            getattr(Prompter, prompter_name)
        ):
            return getattr(Prompter, prompter_name)(**prompter_args)
        return Prompter.default()

    @staticmethod
    def default():
        return Prompter.role_content_dict()

    @staticmethod
    def batched_role_content_dict(*args, **kwargs):
        base = Prompter.role_content_dict(*args, **kwargs)

        def batched(messages):
            result = base(messages)
            return {key: [result[key]] for key in result}

        return batched

    @staticmethod
    def role_content_dict(
        message_key: str = "messages",
        role_key: str = "role",
        content_key: str = "content",
        system_role: str = "system",
        user_role: str = "user",
        agent_role: str = "agent",
    ):
        def prompter(messages: List[Dict[str, str]]):
            nonlocal message_key, role_key, content_key, system_role, user_role, agent_role
            role_dict = {
                "system": system_role,
                "user": user_role,
                "agent": agent_role,
            }
            prompt = []
            for i, item in enumerate(messages):
                # print(i, item, file=open("debug.txt", 'a'))
                prompt.append(
                    {role_key: role_dict[item["role"]], content_key: item["content"]}
                )
            return {message_key: prompt}

        return prompter

    @staticmethod
    def prompt_string(
        prefix: str = "",
        suffix: str = "<|agent|>\n",
        system_format: str = "<|system|>\n{content}\n\n",
        user_format: str = "<|user|>\n{content}\n\n",
        agent_format: str = "<|agent|>\n{content}\n\n",
        prompt_key: str = "prompt",
        image_key: str = "image",
        text_context_limit: int = 9776
    ):
        def prompter(messages: List[Dict]):
            nonlocal prefix, suffix, system_format, user_format, agent_format, prompt_key, image_key, text_context_limit
            
            def text_token_estimation(text: str):
                token_count = 0
                text = text.replace("\n\n", "\n").replace("```", "`").replace("##", "#")
                for char in text:
                    if not char.isalnum() and char != " ":
                        token_count += 1
                words = text.split()
                for word in words:
                    char_count = 0
                    for char in word:
                        if char.isalnum():
                            char_count += 1
                    token_count += math.ceil(char_count / 6)
                return token_count
            
            def item_to_prompt(item: Dict):
                prompt, images = "", []
                if item["role"] == "system":
                    prompt += system_format.format(content=item["content"])
                elif item["role"] == "user":
                    if isinstance(item["content"], str):
                        prompt += user_format.format(content=item["content"])
                    elif isinstance(item["content"], list):
                        text_str = ""
                        for content in item["content"]:
                            if content["type"] == "text":
                                text_str += content["text"]
                            else:
                                images.append(content["image_url"]["url"].split("file://")[-1])
                        prompt += user_format.format(content=text_str)
                else:
                    prompt += agent_format.format(content=item["content"])
                return prompt, images
            
            prompt = prefix
            images = []
            for item in messages[:5]:
                item_prompt, item_images = item_to_prompt(item)
                prompt += item_prompt
                images += item_images
            if len(messages) > 5:
                prompt_tail, images_tail = item_to_prompt(messages[-1])
                for index in range(len(messages)-2, 4, -2):
                    agent_item = messages[index]
                    agent_prompt, agent_images = item_to_prompt(agent_item)
                    user_item = messages[index-1]
                    user_prompt, user_images = item_to_prompt(user_item)
                    if text_token_estimation(prompt + user_prompt + agent_prompt + prompt_tail) > text_context_limit:
                        prompt_tail = "\n\n** Earlier trajectory has been truncated **\n\n" + prompt_tail
                        break
                    prompt_tail = user_prompt + agent_prompt + prompt_tail
                    images_tail = user_images + agent_images + images_tail
                prompt += prompt_tail
                images += images_tail
            prompt += suffix
            if len(images) != 1:
                raise Exception("Only one image is supported")
            return [
                {prompt_key: prompt},
                {image_key: open(images[0], "rb")}
            ]

        return prompter

    @staticmethod
    def claude():
        # todo (YG): currently it assumes the content is always a string, but it can be a list for multimodal support
        return Prompter.prompt_string(
            prefix="",
            suffix="Assistant:",
            user_format="Human: {content}\n\n",
            agent_format="Assistant: {content}\n\n",
        )

    @staticmethod
    def palm():
        def prompter(messages):
            return {"instances": [
                Prompter.role_content_dict("messages", "author", "content", "user", "bot")(messages)
            ]}
        return prompter


def check_context_limit(content: str):
    content = content.lower()
    and_words = [
        ["prompt", "context", "tokens"],
        [
            "limit",
            "exceed",
            "max",
            "long",
            "much",
            "many",
            "reach",
            "over",
            "up",
            "beyond",
        ],
    ]
    rule = AndRule(
        [
            OrRule([ContainRule(word) for word in and_words[i]])
            for i in range(len(and_words))
        ]
    )
    return rule.check(content)


class HTTPAgent(AgentClient):
    def __init__(
        self,
        url,
        proxies=None,
        data=None,
        body=None,
        headers=None,
        return_format="{response}",
        prompter=None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.url = url
        self.proxies = proxies or {}
        self.headers = headers or {}
        self.data = data or {}
        self.body = body or {}
        self.return_format = return_format
        self.prompter = Prompter.get_prompter(prompter)
        self.prompter_type = prompter.get("name", "role_content_dict")
        if not self.url:
            raise Exception("Please set 'url' parameter")

    def _handle_history(self, history: List[dict]) -> Dict[str, Any]:
        return self.prompter(history)

    def inference(self, history: List[dict]) -> str:
        if self.prompter_type == "role_content_dict":
            history = replace_image_url(history, keep_path=False, throw_details=False)
        else:
            history = replace_image_url(history, keep_path=True, throw_details=True)
        for _ in range(10):
            try:
                if self.prompter_type == "role_content_dict":
                    body = self.body.copy()
                    body.update(self._handle_history(history))
                    with no_ssl_verification():
                        resp = requests.post(
                            self.url, json=body, headers=self.headers, proxies=self.proxies, timeout=180
                        )
                else:
                    messages = self._handle_history(history)
                    data = self.data.copy()
                    data.update(messages[0])
                    with no_ssl_verification():
                        resp = requests.post(
                            self.url, data=data, files=messages[1], headers=self.headers, proxies=self.proxies, timeout=180
                        )
                # print(resp.status_code, resp.text)
                if resp.status_code != 200:
                    # print(resp.text)
                    if check_context_limit(resp.text):
                        raise AgentContextLimitException(resp.text)
                    else:
                        raise Exception(
                            f"Invalid status code {resp.status_code}:\n\n{resp.text}"
                        )
            except AgentClientException as e:
                raise e
            except Exception as e:
                print("Warning: ", e)
                pass
            else:
                resp = resp.json()
                return self.return_format.format(response=resp)
            time.sleep(_ + 1)
        raise Exception("Failed.")
