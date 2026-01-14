"""
Analyze AdWave pages to understand their structure.
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
from browser_use import Agent, BrowserProfile

load_dotenv()

from core.browser_agent import create_llm
from core.config import Config


async def analyze_after_login(page_name: str, url: str, config: Config, llm):
    """Login and analyze a page."""

    task = f"""
1. 访问 {config.login_url}
2. 在电邮输入框输入 {{email}}
3. 在密码输入框输入 {{password}}
4. 点击"登入"按钮
5. 等待跳转后，访问 {url}
6. 描述页面上的主要元素：
   - 页面标题
   - 导航菜单
   - 主要按钮
   - 表格/列表
   - 数据展示区
用中文简洁回答。
"""

    agent = Agent(
        task=task,
        llm=llm,
        browser_profile=BrowserProfile(headless=True),
        sensitive_data=config.credentials,
        max_steps=12,
    )

    result = await agent.run()
    return str(result)


async def main():
    config = Config()
    llm = create_llm(config.llm_config)

    print("=" * 60)
    print("分析 Campaign 页面 (登录后)")
    print("=" * 60)

    result = await analyze_after_login("Campaign", config.campaign_url, config, llm)

    # Extract the final result
    if "extracted_content=" in result:
        # Find the last extracted_content
        parts = result.split("extracted_content='")
        if len(parts) > 1:
            last_content = parts[-1].split("'")[0]
            print(f"\n结果:\n{last_content}")
    else:
        print(result)


if __name__ == "__main__":
    asyncio.run(main())
