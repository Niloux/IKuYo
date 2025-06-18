import logging
import re
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup, Tag

# 配置日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


# 配置常量
class Config:
    BASE_URL = "https://mikanani.me"
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    }
    TIMEOUT = 10
    MAX_RETRIES = 3


# CSS选择器和正则表达式
class Selectors:
    BANGUMI_LINKS = 'div.m-week-square a[href*="/Home/Bangumi/"]'
    BANGUMI_ID_PATTERN = r"/Home/Bangumi/(\d+)"
    BANGUMI_SUBJECT_PATTERN = r"/subject/(\d+)"
    DATE_PATTERN = r"\d+/\d+/\d+"
    EXCLUDED_GROUPS = {"主页", "订阅", "列表", "搜索站内", "取消"}


class MikanSpider:
    """Mikan动画网站爬虫"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(Config.HEADERS)

    def fetch_html(self, url: str) -> str:
        """获取网页HTML内容"""
        for attempt in range(Config.MAX_RETRIES):
            try:
                response = self.session.get(url, timeout=Config.TIMEOUT)
                response.raise_for_status()
                return response.text
            except requests.RequestException as e:
                logger.warning(f"请求失败 (尝试 {attempt + 1}/{Config.MAX_RETRIES}): {e}")
                if attempt == Config.MAX_RETRIES - 1:
                    raise
        raise requests.RequestException("所有重试都失败了")

    def parse_bangumi_list_page(self, html: str) -> List[Tuple[str, str, Optional[int]]]:
        """解析番组列表页面"""
        soup = BeautifulSoup(html, "html.parser")
        bangumi_links = []

        for link in soup.select(Selectors.BANGUMI_LINKS):
            href = link.get("href")
            title = link.get("title", "")

            if not (href and isinstance(href, str) and "/Home/Bangumi/" in href):
                continue

            mikan_id = self._extract_mikan_id(href)
            full_url = urljoin(Config.BASE_URL, href)
            bangumi_links.append((full_url, title, mikan_id))

        return bangumi_links

    def parse_bangumi_detail_page(self, html: str) -> Dict:
        """解析番组详情页面"""
        soup = BeautifulSoup(html, "html.parser")

        return {
            "title": self._extract_title(soup),
            "broadcast_day": self._extract_broadcast_day(soup),
            "broadcast_start": self._extract_broadcast_start(soup),
            "official_website": self._extract_official_website(soup),
            "bangumi_url": self._extract_bangumi_url(soup),
            "bangumi_id": self._extract_bangumi_id(soup),
            "description": self._extract_description(soup),
            "subtitle_groups": self._extract_subtitle_groups(soup),
            "resources_by_group": self._extract_resources(soup),
        }

    def _extract_mikan_id(self, href: str) -> Optional[int]:
        """提取Mikan ID"""
        match = re.search(Selectors.BANGUMI_ID_PATTERN, href)
        return int(match.group(1)) if match else None

    def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        """提取标题"""
        # 方式1：页面title标签
        if soup.title:
            title = soup.title.get_text(strip=True)
            if title.startswith("Mikan Project - "):
                title = title.replace("Mikan Project - ", "")
            return title

        # 方式2：查找页面主标题
        for heading in soup.find_all(["h1", "h2", "h3"]):
            if heading.get_text(strip=True):
                return heading.get_text(strip=True)

        return None

    def _extract_broadcast_day(self, soup: BeautifulSoup) -> Optional[str]:
        """提取放送日期"""
        for text in soup.stripped_strings:
            if text.startswith("放送日期："):
                return text.replace("放送日期：", "").strip()
        return None

    def _extract_broadcast_start(self, soup: BeautifulSoup) -> Optional[str]:
        """提取放送开始时间"""
        for text in soup.stripped_strings:
            if text.startswith("放送开始："):
                return text.replace("放送开始：", "").strip()
        return None

    def _extract_official_website(self, soup: BeautifulSoup) -> Optional[str]:
        """提取官方网站"""
        for text in soup.stripped_strings:
            if "官方网站" in text:
                for link in soup.find_all("a", href=True):
                    if link.get_text(strip=True) and "官方网站" in link.parent.get_text():
                        return link["href"]
                break
        return None

    def _extract_bangumi_url(self, soup: BeautifulSoup) -> Optional[str]:
        """提取Bangumi链接"""
        for link in soup.find_all("a", href=True):
            if "bgm.tv/subject/" in link["href"]:
                return link["href"]
        return None

    def _extract_bangumi_id(self, soup: BeautifulSoup) -> Optional[int]:
        """提取Bangumi ID"""
        bangumi_url = self._extract_bangumi_url(soup)
        if bangumi_url:
            match = re.search(Selectors.BANGUMI_SUBJECT_PATTERN, bangumi_url)
            return int(match.group(1)) if match else None
        return None

    def _extract_description(self, soup: BeautifulSoup) -> Optional[str]:
        """提取简介"""
        for text in soup.stripped_strings:
            if len(text) > 50:  # 简介通常较长
                return text
        return None

    def _extract_subtitle_groups(self, soup: BeautifulSoup) -> List[str]:
        """提取字幕组列表"""
        subtitle_groups = []

        for text in soup.stripped_strings:
            if "字幕组列表" in text:
                for ul in soup.find_all("ul"):
                    for li in ul.find_all("li"):
                        group_name = li.get_text(strip=True)
                        if self._is_valid_subtitle_group(group_name):
                            group_name = self._clean_subtitle_group_name(group_name)
                            subtitle_groups.append(group_name)
                break

        return subtitle_groups

    def _is_valid_subtitle_group(self, group_name: str) -> bool:
        """检查是否为有效的字幕组名称"""
        return bool(
            group_name and len(group_name) > 1 and group_name not in Selectors.EXCLUDED_GROUPS
        )

    def _clean_subtitle_group_name(self, group_name: str) -> str:
        """清理字幕组名称，去除日期信息"""
        if re.search(Selectors.DATE_PATTERN, group_name):
            return re.sub(r"\s*\d+/\d+/\d+.*", "", group_name)
        return group_name

    def _extract_resources(self, soup: BeautifulSoup) -> Dict[str, List[Dict]]:
        """提取资源列表，按字幕组分组"""
        resources_by_group = {}

        # 先获取所有字幕组名称
        subtitle_groups = self._extract_subtitle_groups(soup)

        # 为每个字幕组提取资源
        for group_name in subtitle_groups:
            group_resources = self._extract_group_resources(soup, group_name)
            if group_resources:
                resources_by_group[group_name] = group_resources

        return resources_by_group

    def _extract_group_resources(self, soup: BeautifulSoup, group_name: str) -> List[Dict]:
        """提取指定字幕组的资源列表"""
        resources = []

        # 查找包含该字幕组名称的表格
        for table in soup.find_all("table"):
            if not isinstance(table, Tag):
                continue

            # 检查表格是否属于该字幕组
            table_parent = table.parent
            if table_parent:
                parent_text = table_parent.get_text()
                if group_name in parent_text:
                    # 解析该表格的资源
                    for row in table.find_all("tr")[1:]:  # 跳过表头
                        if not isinstance(row, Tag):
                            continue

                        cols = row.find_all("td")
                        if len(cols) >= 4:
                            resource = {
                                "title": cols[0].get_text(strip=True) or "",
                                "file_size": cols[1].get_text(strip=True) or "",
                                "release_date": cols[2].get_text(strip=True) or "",
                                "download_url": self._extract_download_url(cols[3]),
                                "subtitle_group": group_name,
                            }
                            resources.append(resource)

        return resources

    def _extract_download_url(self, col: Tag) -> Optional[str]:
        """提取下载链接"""
        link = col.find("a")
        if link and isinstance(link, Tag) and link.get("href"):
            return link.get("href")
        return None

    def crawl_bangumi_list(self, limit: Optional[int] = None) -> List[Dict]:
        """爬取番组列表"""
        try:
            list_url = f"{Config.BASE_URL}/Home"
            html = self.fetch_html(list_url)
            bangumi_links = self.parse_bangumi_list_page(html)

            logger.info(f"发现 {len(bangumi_links)} 个番组")

            results = []
            for url, title, mikan_id in bangumi_links[:limit]:
                try:
                    logger.info(f"爬取详情页: {title} (ID: {mikan_id})")
                    detail_html = self.fetch_html(url)
                    detail = self.parse_bangumi_detail_page(detail_html)
                    detail["mikan_id"] = mikan_id
                    results.append(detail)
                except Exception as e:
                    logger.error(f"爬取详情页失败 {url}: {e}")

            return results

        except Exception as e:
            logger.error(f"爬取番组列表失败: {e}")
            return []


def main():
    """主函数"""
    spider = MikanSpider()
    results = spider.crawl_bangumi_list(limit=3)

    for result in results:
        print(f"标题: {result['title']}")
        print(f"Mikan ID: {result['mikan_id']}")
        print(f"Bangumi ID: {result['bangumi_id']}")
        print(f"字幕组数量: {len(result['subtitle_groups'])}")

        # 显示按字幕组分组的资源统计
        total_resources = 0
        for group_name, resources in result["resources_by_group"].items():
            print(f"  {group_name}: {len(resources)} 个资源")
            total_resources += len(resources)
        print(f"总资源数量: {total_resources}")
        print("-" * 50)


if __name__ == "__main__":
    main()
