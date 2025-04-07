import os, json
import requests

"""
工具函数

- 首先要在 tools 中添加工具的描述信息
- 然后在 tools 中添加工具的具体实现

- https://serper.dev/dashboard
"""


class Tools:
    def __init__(self) -> None:
        self.toolConfig = self._tools()

    def _tools(self):
        tools = [
            # {
            #     "name_for_human": "谷歌搜索",
            #     "name_for_model": "google_search",
            #     "description_for_model": "谷歌搜索是一个通用搜索引擎，可用于访问互联网、查询百科知识、了解时事新闻等。",
            #     "parameters": [
            #         {
            #             "name": "search_query",
            #             "description": "搜索关键词或短语",
            #             "required": True,
            #             "schema": {"type": "string"},
            #         }
            #     ],
            # }
            {
                "name_for_human": "必应搜索",
                "name_for_model": "bing_search",
                "description_for_model": "必应搜索是一个通用搜索引擎，可用于访问互联网、查询百科知识、了解时事新闻等。",
                "parameters": [
                    {
                        "name": "search_query",
                        "description": "搜索关键词或短语",
                        "required": True,
                        "schema": {"type": "string"},
                    }
                ],
            }
        ]
        return tools

    def google_search(self, search_query: str):
        url = "https://google.serper.dev/search"

        payload = json.dumps({"q": search_query})
        headers = {"X-API-KEY": "修改为你自己的key", "Content-Type": "application/json"}

        response = requests.request("POST", url, headers=headers, data=payload).json()

        return response["organic"][0]["snippet"]

    def _get_page_content(
        self,
        pages: list,
        page_index: int = 0,
        max_chars: int = 5000,
    ):
        from tinyAgent.web_search import get_page_content

        try:
            body = get_page_content(pages[page_index]["link"], max_chars=max_chars)
            return body
        except:
            page_index += 1
            if page_index < len(pages):
                return self._get_page_content(pages, page_index)

    def bing_search(self, search_query: str):
        from tinyAgent.web_search import (
            search_bing,
            parse_bing_results,
            get_page_content,
        )

        results = parse_bing_results(search_bing(search_query, False))
        if len(results) > 0:
            # body = get_page_content(results[0]["link"], max_chars=5000)
            body = self._get_page_content(results, max_chars=5000)
            return body
        else:
            return ""
