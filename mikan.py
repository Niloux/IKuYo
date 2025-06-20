import datetime
import logging
import re
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup, Tag

from models import Anime, CrawlLog, Resource, SubtitleGroup

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
                    if (
                        isinstance(link, Tag)
                        and link.get_text(strip=True)
                        and link.parent
                        and isinstance(link.parent, Tag)
                        and "官方网站" in link.parent.get_text()
                    ):
                        href = link.get("href")
                        return str(href) if href else None
                break
        return None

    def _extract_bangumi_url(self, soup: BeautifulSoup) -> Optional[str]:
        """提取Bangumi链接"""
        for link in soup.find_all("a", href=True):
            if isinstance(link, Tag):
                href = link.get("href")
                if href and "bgm.tv/subject/" in str(href):
                    return str(href)
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

    def _extract_subtitle_groups(self, soup: BeautifulSoup) -> List[Dict]:
        """提取字幕组列表，包含ID和名称"""
        subtitle_groups = []

        for text in soup.stripped_strings:
            if "字幕组列表" in text:
                for ul in soup.find_all("ul"):
                    if isinstance(ul, Tag):
                        for li in ul.find_all("li"):
                            if isinstance(li, Tag):
                                # 查找字幕组链接
                                subgroup_link = li.find("a", class_="subgroup-name")
                                if subgroup_link and isinstance(subgroup_link, Tag):
                                    # 提取字幕组ID
                                    class_name = subgroup_link.get_attribute_list("class")
                                    subgroup_id = None
                                    if class_name:
                                        for cls in class_name:
                                            if isinstance(cls, str) and cls.startswith(
                                                "subgroup-"
                                            ):
                                                try:
                                                    subgroup_id = int(cls.replace("subgroup-", ""))
                                                    break
                                                except ValueError:
                                                    continue

                                    # 提取字幕组名称
                                    group_name = subgroup_link.get_text(strip=True)

                                    if subgroup_id and self._is_valid_subtitle_group(group_name):
                                        group_name = self._clean_subtitle_group_name(group_name)
                                        subtitle_groups.append({
                                            "id": subgroup_id,
                                            "name": group_name,
                                        })
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

        # 先获取所有字幕组信息
        subtitle_groups = self._extract_subtitle_groups(soup)

        # 为每个字幕组提取资源
        for group_info in subtitle_groups:
            group_name = group_info["name"]
            group_id = group_info["id"]
            group_resources = self._extract_group_resources(soup, group_name, group_id)
            if group_resources:
                resources_by_group[group_name] = group_resources

        return resources_by_group

    def _extract_group_resources(
        self, soup: BeautifulSoup, group_name: str, group_id: int
    ) -> List[Dict]:
        """提取指定字幕组的资源列表"""
        resources = []

        # 查找包含该字幕组名称的表格
        for table in soup.find_all("table"):
            if not isinstance(table, Tag):
                continue

            # 检查表格是否属于该字幕组
            table_parent = table.parent
            if table_parent and isinstance(table_parent, Tag):
                parent_text = table_parent.get_text()
                if group_name in parent_text:
                    # 解析该表格的资源
                    for row in table.find_all("tr")[1:]:  # 跳过表头
                        if not isinstance(row, Tag):
                            continue

                        cols = row.find_all("td")
                        if len(cols) >= 5:  # 应该有5列：标题、大小、时间、下载、播放
                            resource = {
                                "title": cols[0].get_text(strip=True) or "",
                                "file_size": cols[1].get_text(strip=True) or "",
                                "release_date": cols[2].get_text(strip=True) or "",
                                "magnet_url": self._extract_magnet_url(cols[0]),
                                "torrent_url": self._extract_torrent_url(cols[3]),
                                "play_url": self._extract_play_url(cols[4]),
                                "subtitle_group": group_name,
                                "subtitle_group_id": group_id,
                            }
                            resources.append(resource)

        return resources

    def _extract_magnet_url(self, col: Any) -> Optional[str]:
        """提取磁力链接"""
        if not isinstance(col, Tag):
            return None
        magnet_link = col.find("a", class_="js-magnet")
        if magnet_link and isinstance(magnet_link, Tag):
            magnet_url = magnet_link.get("data-clipboard-text")
            return str(magnet_url) if magnet_url else None
        return None

    def _extract_torrent_url(self, col: Any) -> Optional[str]:
        """提取种子文件链接"""
        if not isinstance(col, Tag):
            return None
        torrent_link = col.find("a")
        if torrent_link and isinstance(torrent_link, Tag):
            torrent_url = torrent_link.get("href")
            if torrent_url and "Download" in str(torrent_url):
                return urljoin(Config.BASE_URL, str(torrent_url))
        return None

    def _extract_play_url(self, col: Any) -> Optional[str]:
        """提取播放链接"""
        if not isinstance(col, Tag):
            return None
        play_link = col.find("a")
        if play_link and isinstance(play_link, Tag):
            play_url = play_link.get("href")
            return str(play_url) if play_url else None
        return None

    def _extract_magnet_hash(self, magnet_url: Optional[str]) -> Optional[str]:
        """从磁力链接中提取hash值"""
        if not magnet_url:
            return None
        match = re.search(r"btih:([a-fA-F0-9]{40})", magnet_url)
        return match.group(1) if match else None

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

    # 创建爬取日志
    crawl_log = CrawlLog(spider_name="mikan_spider")

    try:
        results = spider.crawl_bangumi_list(limit=3)

        print("=" * 60)
        print("数据验证结果")
        print("=" * 60)

        for i, result in enumerate(results, 1):
            print(f"\n【动画 {i}】")
            print("-" * 40)

            # 验证Anime模型数据
            mikan_id = result.get("mikan_id")
            if mikan_id is None:
                print("❌ 错误: mikan_id 为 None，跳过此动画")
                continue

            anime = Anime(
                mikan_id=mikan_id,
                bangumi_id=result.get("bangumi_id"),
                title=result.get("title", ""),
                broadcast_day=result.get("broadcast_day"),
                broadcast_start=result.get("broadcast_start"),
                official_website=result.get("official_website"),
                bangumi_url=result.get("bangumi_url"),
                description=result.get("description"),
            )

            print("✅ Anime模型验证:")
            print(f"   mikan_id: {anime.mikan_id}")
            print(f"   bangumi_id: {anime.bangumi_id}")
            print(f"   title: {anime.title}")
            print(f"   broadcast_day: {anime.broadcast_day}")
            print(f"   broadcast_start: {anime.broadcast_start}")
            print(f"   official_website: {anime.official_website}")
            print(f"   bangumi_url: {anime.bangumi_url}")
            print(
                f"   description: {anime.description[:100] + '...' if anime.description and len(anime.description) > 100 else anime.description}"
            )

            # 验证SubtitleGroup模型数据
            subtitle_groups = []
            for group_info in result.get("subtitle_groups", []):
                subtitle_group = SubtitleGroup(name=group_info["name"])
                subtitle_groups.append(subtitle_group)

            print(f"\n✅ SubtitleGroup模型验证 (共{len(subtitle_groups)}个):")
            for j, group in enumerate(subtitle_groups, 1):
                group_info = result.get("subtitle_groups", [])[j - 1]
                print(f"   {j}. {group.name} (ID: {group_info['id']})")

            # 验证Resource模型数据
            resources = []
            resources_by_group = result.get("resources_by_group", {})

            for group_name, group_resources in resources_by_group.items():
                for resource_data in group_resources:
                    # 尝试从标题中提取集数
                    episode_number = 1  # 默认值
                    title = resource_data.get("title", "")

                    # 简单的集数提取逻辑
                    episode_match = re.search(r"(\d+)", title)
                    if episode_match:
                        episode_number = int(episode_match.group(1))

                    resource = Resource(
                        anime_id=anime.mikan_id,  # 使用mikan_id作为anime_id
                        subtitle_group_id=resource_data.get(
                            "subtitle_group_id", 1
                        ),  # 使用实际的subtitle_group_id
                        episode_number=episode_number,
                        title=title,
                        file_size=resource_data.get("file_size"),
                        download_url=resource_data.get("magnet_url"),  # 使用磁力链接作为下载链接
                        magnet_hash=spider._extract_magnet_hash(resource_data.get("magnet_url")),
                        release_date=resource_data.get("release_date"),
                    )
                    resources.append(resource)

            print(f"\n✅ Resource模型验证 (共{len(resources)}个):")
            for j, resource in enumerate(resources[:5], 1):  # 只显示前5个
                print(f"   {j}. {resource.title}")
                print(f"      集数: {resource.episode_number}")
                print(f"      大小: {resource.file_size}")
                print(f"      发布日期: {resource.release_date}")
                print(f"      字幕组ID: {resource.subtitle_group_id}")
                print(
                    f"      磁力链接: {resource.download_url[:50] + '...' if resource.download_url and len(resource.download_url) > 50 else resource.download_url}"
                )

            if len(resources) > 5:
                print(f"   ... 还有 {len(resources) - 5} 个资源")

            # 更新爬取日志
            crawl_log.items_count += len(resources)
            crawl_log.status = "success"

            print("\n📊 统计信息:")
            print(f"   字幕组数量: {len(subtitle_groups)}")
            print(f"   资源总数: {len(resources)}")

        # 最终日志
        crawl_log.end_time = datetime.datetime.now().isoformat()
        print("\n✅ 爬取完成:")
        print(f"   总资源数: {crawl_log.items_count}")
        print(f"   开始时间: {crawl_log.start_time}")
        print(f"   结束时间: {crawl_log.end_time}")
        print(f"   状态: {crawl_log.status}")

    except Exception as e:
        crawl_log.status = "error"
        crawl_log.error_message = str(e)
        crawl_log.end_time = datetime.datetime.now().isoformat()
        print(f"❌ 爬取失败: {e}")
        print(f"   错误信息: {crawl_log.error_message}")
        print(f"   状态: {crawl_log.status}")


if __name__ == "__main__":
    main()
