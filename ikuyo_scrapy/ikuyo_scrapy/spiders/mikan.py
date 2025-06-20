import datetime
import re
from urllib.parse import urljoin

from scrapy import Request, Spider

from ikuyo_scrapy.items import AnimeItem, CrawlLogItem, ResourceItem, SubtitleGroupItem


class MikanSpider(Spider):
    name = "mikan"
    allowed_domains = ["mikanani.me"]
    start_urls = ["https://mikanani.me/Home"]

    # 配置常量
    BASE_URL = "https://mikanani.me"
    MAX_ANIME_LIMIT = 3  # 限制爬取的动画数量

    def __init__(self, limit=None, *args, **kwargs):
        super(MikanSpider, self).__init__(*args, **kwargs)
        self.limit = int(limit) if limit else self.MAX_ANIME_LIMIT
        self.crawl_log = CrawlLogItem()
        self.crawl_log["spider_name"] = self.name
        self.crawl_log["start_time"] = datetime.datetime.now().isoformat()
        self.crawl_log["status"] = "running"
        self.crawl_log["items_count"] = 0

    def parse(self, response):
        """解析首页，获取动画列表"""
        self.logger.info("开始解析动画列表页面")

        # 查找动画链接
        anime_links = response.css('div.m-week-square a[href*="/Home/Bangumi/"]')

        for link in anime_links[: self.limit]:
            href = link.attrib.get("href")
            title = link.attrib.get("title", "")

            if href and "/Home/Bangumi/" in href:
                mikan_id = self._extract_mikan_id(href)
                if mikan_id:
                    full_url = urljoin(self.BASE_URL, href)
                    self.logger.info(f"发现动画: {title} (ID: {mikan_id})")

                    yield Request(
                        url=full_url,
                        callback=self.parse_anime_detail,
                        meta={"mikan_id": mikan_id, "title": title},
                    )

    def parse_anime_detail(self, response):
        """解析动画详情页面"""
        mikan_id = response.meta["mikan_id"]
        title = response.meta["title"]

        self.logger.info(f"解析动画详情: {title} (ID: {mikan_id})")

        # 创建Anime Item
        anime = AnimeItem()
        anime["mikan_id"] = mikan_id
        anime["title"] = self._extract_title(response)
        anime["bangumi_id"] = self._extract_bangumi_id(response)
        anime["broadcast_day"] = self._extract_broadcast_day(response)
        anime["broadcast_start"] = self._extract_broadcast_start(response)
        anime["official_website"] = self._extract_official_website(response)
        anime["bangumi_url"] = self._extract_bangumi_url(response)
        anime["description"] = self._extract_description(response)
        anime["created_at"] = datetime.datetime.now().isoformat()
        anime["updated_at"] = datetime.datetime.now().isoformat()

        yield anime

        # 提取字幕组信息
        subtitle_groups = self._extract_subtitle_groups(response)
        for group in subtitle_groups:
            yield SubtitleGroupItem(group)

        # 提取资源信息
        resources = self._extract_resources(response, mikan_id, subtitle_groups)
        for resource in resources:
            yield ResourceItem(resource)

        # 更新爬取日志
        self.crawl_log["items_count"] += len(resources)
        self.crawl_log["mikan_id"] = mikan_id

    def _extract_mikan_id(self, href):
        """提取Mikan ID"""
        match = re.search(r"/Home/Bangumi/(\d+)", href)
        return int(match.group(1)) if match else None

    def _extract_title(self, response):
        """提取标题"""
        # 从页面title标签提取
        title = response.css("title::text").get()
        if title and title.startswith("Mikan Project - "):
            title = title.replace("Mikan Project - ", "")
        return title

    def _extract_bangumi_id(self, response):
        """提取Bangumi ID"""
        bangumi_url = self._extract_bangumi_url(response)
        if bangumi_url:
            match = re.search(r"/subject/(\d+)", bangumi_url)
            return int(match.group(1)) if match else None
        return None

    def _extract_bangumi_url(self, response):
        """提取Bangumi链接"""
        bangumi_link = response.css('a[href*="bgm.tv/subject/"]::attr(href)').get()
        return bangumi_link

    def _extract_broadcast_day(self, response):
        """提取放送日期"""
        # 查找包含"放送日期："的文本
        for text in response.css("*::text").getall():
            if text and "放送日期：" in text:
                return text.replace("放送日期：", "").strip()
        return None

    def _extract_broadcast_start(self, response):
        """提取放送开始时间"""
        for text in response.css("*::text").getall():
            if text and "放送开始：" in text:
                return text.replace("放送开始：", "").strip()
        return None

    def _extract_official_website(self, response):
        """提取官方网站"""
        # 尝试多种方法提取官方网站
        extraction_methods = [
            self._find_official_links_by_text,
            self._find_official_links_in_sections,
            self._find_external_links,
            self._find_specific_domains,
        ]

        for method in extraction_methods:
            result = method(response)
            if result:
                return result

        return None

    def _find_official_links_by_text(self, response):
        """通过文本查找官方网站链接"""
        # 查找包含"官方网站"文本的链接
        official_links = response.xpath(
            '//a[contains(text(), "官方网站") or contains(following-sibling::text(), "官方网站")]/@href'  # noqa: E501
        ).getall()

        # 查找在"官方网站"文本附近的链接
        for text_node in response.xpath('//text()[contains(., "官方网站")]'):
            parent = text_node.xpath("..")
            links = parent.xpath(".//a/@href").getall()
            if links:
                return links[0]

        return official_links[0] if official_links else None

    def _find_official_links_in_sections(self, response):
        """在包含官方网站的段落中查找链接"""
        official_sections = response.xpath('//p[contains(text(), "官方网站")]//a/@href').getall()
        return official_sections[0] if official_sections else None

    def _find_external_links(self, response):
        """查找外部链接"""
        all_links = response.xpath("//a/@href").getall()
        external_links = [
            link
            for link in all_links
            if link
            and (link.startswith("http://") or link.startswith("https://"))
            and "mikanani.me" not in link
            and "bgm.tv" not in link
        ]

        # 如果只有一个外部链接，可能是官方网站
        return external_links[0] if len(external_links) == 1 else None

    def _find_specific_domains(self, response):
        """查找特定域名的链接"""
        common_domains = ["anime-chiikawa.jp", "www.anime-chiikawa.jp"]
        for domain in common_domains:
            domain_links = response.xpath(f'//a[contains(@href, "{domain}")]/@href').getall()
            if domain_links:
                return domain_links[0]
        return None

    def _extract_description(self, response):
        """提取简介"""
        # 查找"概况介绍"部分的文本
        # 使用XPath查找包含"概况介绍"的文本节点
        intro_texts = response.xpath(
            '//text()[contains(., "概况介绍")]/following::text()'
        ).getall()

        # 过滤并清理文本
        for text in intro_texts:
            text = text.strip()
            # 跳过空文本、JavaScript代码和太短的文本
            if (
                text
                and len(text) > 20
                and not text.startswith("(function")
                and not text.startswith("ga(")
                and not text.startswith("Powered by")
                and not text.startswith("Cooperate by")
            ):
                return text

        # 备用方法：查找较长的文本段落
        for text in response.css("*::text").getall():
            text = text.strip()
            if (
                text
                and len(text) > 50
                and not text.startswith("(function")
                and not text.startswith("ga(")
                and not text.startswith("Powered by")
                and not text.startswith("Cooperate by")
            ):
                return text

        return None

    def _extract_subtitle_groups(self, response):
        """提取字幕组列表"""
        subtitle_groups = []

        # 查找字幕组链接
        subgroup_links = response.css("a.subgroup-name")

        for link in subgroup_links:
            class_attr = link.attrib.get("class", "")
            if isinstance(class_attr, list):
                class_attr = " ".join(class_attr)

            # 提取字幕组ID
            subgroup_id = None
            for cls in class_attr.split():
                if cls.startswith("subgroup-"):
                    try:
                        subgroup_id = int(cls.replace("subgroup-", ""))
                        break
                    except ValueError:
                        continue

            if subgroup_id:
                name = link.css("::text").get().strip()
                if name and len(name) > 1:
                    subtitle_groups.append({
                        "id": subgroup_id,
                        "name": name,
                        "created_at": datetime.datetime.now().isoformat(),
                    })

        return subtitle_groups

    def _extract_resources(self, response, mikan_id, subtitle_groups):
        """提取资源列表"""
        resources = []

        # 创建字幕组名称到ID的映射
        group_name_to_id = {group["name"]: group["id"] for group in subtitle_groups}

        # 查找资源表格
        tables = response.css("table.table-striped")

        for table in tables:
            # 检查表格是否属于某个字幕组
            table_parent = table.xpath("..")
            parent_text = " ".join(table_parent.css("*::text").getall())

            # 找到对应的字幕组
            group_name = None
            group_id = None
            for name, gid in group_name_to_id.items():
                if name in parent_text:
                    group_name = name
                    group_id = gid
                    break

            if not group_name:
                continue

            # 解析表格行
            rows = table.css("tbody tr")
            for row in rows:
                cols = row.css("td")
                if len(cols) >= 5:
                    resource = self._parse_resource_row(cols, mikan_id, group_id, group_name)
                    if resource:
                        resources.append(resource)

        return resources

    def _parse_resource_row(self, cols, mikan_id, group_id, group_name):
        """解析资源行"""
        try:
            # 提取标题和磁力链接
            title_col = cols[0]
            title = title_col.css("a.magnet-link-wrap::text").get()
            if not title:
                title = title_col.css("::text").get()

            # 提取磁力链接
            magnet_link = title_col.css("a.js-magnet::attr(data-clipboard-text)").get()

            # 提取种子链接
            torrent_link = cols[3].css("a::attr(href)").get()
            if torrent_link and "Download" in torrent_link:
                torrent_url = urljoin(self.BASE_URL, torrent_link)
            else:
                torrent_url = None

            # 提取播放链接
            play_link = cols[4].css("a::attr(href)").get()

            # 提取其他信息
            file_size = cols[1].css("::text").get().strip()
            release_date = cols[2].css("::text").get().strip()

            # 提取集数
            episode_number = 1
            if title:
                episode_match = re.search(r"(\d+)", title)
                if episode_match:
                    episode_number = int(episode_match.group(1))

            # 提取磁力链接hash
            magnet_hash = None
            if magnet_link:
                hash_match = re.search(r"btih:([a-fA-F0-9]{40})", magnet_link)
                if hash_match:
                    magnet_hash = hash_match.group(1)

            return {
                "mikan_id": mikan_id,
                "subtitle_group_id": group_id,
                "episode_number": episode_number,
                "title": title.strip() if title else "",
                "file_size": file_size,
                "magnet_url": magnet_link,
                "torrent_url": torrent_url,
                "play_url": play_link,
                "magnet_hash": magnet_hash,
                "release_date": release_date,
                "created_at": datetime.datetime.now().isoformat(),
            }
        except Exception as e:
            self.logger.error(f"解析资源行失败: {e}")
            return None

    def closed(self, reason):
        """爬虫结束时记录日志"""
        self.crawl_log["end_time"] = datetime.datetime.now().isoformat()
        self.crawl_log["status"] = "success" if reason == "finished" else "error"
        self.logger.info(
            f"爬虫结束，状态: {self.crawl_log['status']}, 总资源数: {self.crawl_log['items_count']}"  # noqa: E501
        )
