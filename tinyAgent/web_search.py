from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from bs4 import BeautifulSoup


def search_bing(keywords: str, show_ui: bool = False):
    chrome_options = Options()
    if not show_ui:
        chrome_options.add_argument("--headless")  # 无界面模式
        chrome_options.add_argument("--disable-gpu")  # 禁用GPU加速，某些系统/环境需要

    driver = webdriver.Chrome(options=chrome_options)
    try:
        driver.implicitly_wait(5)

        # page_content = driver.page_source

        driver.get("https://cn.bing.com")

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "sb_form_q"))
        )

        text_box = driver.find_element(by=By.ID, value="sb_form_q")

        text_box.send_keys(keywords)
        text_box.send_keys(Keys.ENTER)

        time.sleep(3)
        driver.refresh()

        time.sleep(10)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "b_results"))
        )

        page_content = driver.page_source

        with open("coding/page.html", "w") as f:
            f.write(page_content)

        # print(f'page_content: {page_content}')
    except Exception:
        pass
    driver.quit()
    return page_content


def parse_bing_links(page_content: str):
    links = []
    try:
        soup = BeautifulSoup(page_content, "html.parser")
        li_list = soup.select("#b_results")[0].select("li")
        for li in li_list:
            try:
                a = li.select(".b_tpcn")[0].select("a")[0]
                if "href" in a.attrs:
                    link = a["href"]
                    links.append(link)
            except:
                print(f"parse link error: {li}")
    except Exception as e:
        # print(e)
        pass
    return links


def parse_bing_results(page_content: str):
    results = []
    try:
        soup = BeautifulSoup(page_content, "html.parser")
        li_list = soup.select("#b_results")[0].select("li")
        for li in li_list:
            try:
                a = li.select(".b_tpcn")[0].select("a")[0]
                title = li.select("h2")[0].select("a")[0].text
                snippet = li.select(".b_caption")[0].select("p")[0].text
                if "href" in a.attrs:
                    link = a["href"]
                    results.append(
                        {
                            "title": title,
                            "link": link,
                            "snippet": snippet,
                            "body": "",
                        }
                    )
            except:
                # print(f"parse item error: {li}")
                pass
    except Exception as e:
        # print(e)
        pass
    print(f"search results: {len(results)}")
    return results


def get_page_content(url: str, max_chars: int = 500) -> str:
    import requests

    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.content, "html.parser")
        text = soup.get_text(separator=" ", strip=True)
        words = text.split()
        content = ""
        for word in words:
            if len(content) + len(word) + 1 > max_chars:
                break
            content += " " + word
        return content.strip()
    except Exception as e:
        print(f"Error fetching {url}: {str(e)}")
        return ""


def bing_search(query: str, max_chars: int = 500):
    from web_search import search_bing, parse_bing_results

    from bs4 import BeautifulSoup
    import time

    results = parse_bing_results(search_bing(query, show_ui=True))

    enriched_results = []
    for item in results:
        body = get_page_content(item["link"], max_chars)
        enriched_results.append(
            {
                "title": item["title"],
                "link": item["link"],
                "snippet": item["snippet"],
                "body": body,
            }
        )
        time.sleep(1)  # Be respectful to the servers

    return enriched_results
