import datetime
import re
from urllib.parse import quote, urljoin

from scrapy import Request, Spider

from src.crawler.items import AnimeItem, CrawlLogItem, ResourceItem, SubtitleGroupItem


class MikanSpider(Spider):
    name = "mikan"

    def __init__(
        self,
        config,
        limit=None,
        start_url=None,
        mode=None,
        year=None,
        season=None,
        *args,
        **kwargs,
    ):
        super(MikanSpider, self).__init__(*args, **kwargs)
        self.config = config
        self.limit = limit if limit is not None else getattr(config, "limit", None)
        self.start_url = start_url
        self.mode = mode or getattr(config, "crawl_mode", None) or getattr(config, "mode", None)
        self.year = year or getattr(config, "year", None)
        self.season = season or getattr(config, "season", None)
        self.allowed_domains = getattr(config.site, "allowed_domains", ["mikanani.me"])
        self.start_urls = getattr(config.site, "start_urls", ["https://mikanani.me/Home"])
        self.BASE_URL = getattr(config.site, "base_url", "https://mikanani.me")

        self.logger.info(f"爬取模式: {self.mode}")
        if self.year:
            self.logger.info(f"爬取年份: {self.year}")
        if self.season:
            self.logger.info(f"爬取季度: {self.season}")

        # 初始化爬取日志
        self.crawl_log = CrawlLogItem()
        self.crawl_log["spider_name"] = self.name
        self.crawl_log["start_time"] = datetime.datetime.now().isoformat()
        self.crawl_log["status"] = "running"
        self.crawl_log["items_count"] = 0
        self.crawl_log["crawl_mode"] = self.mode
        self.crawl_log["crawl_year"] = self.year
        self.crawl_log["crawl_season"] = self.season

        # 如果指定了起始URL，直接使用
        if self.start_url:
            self.start_urls = [self.start_url]
            self.logger.info(f"使用指定起始URL: {self.start_url}")

    def parse(self, response):
        """解析首页，根据爬取模式选择不同的解析策略"""
        self.logger.info(f"开始解析，模式: {self.mode}")

        # 如果是指定的起始URL，直接解析详情页
        if self.start_url and "/Home/Bangumi/" in self.start_url:
            mikan_id = self._extract_mikan_id(self.start_url)
            if mikan_id:
                self.logger.info(f"直接解析指定动画 (ID: {mikan_id})")
                yield Request(
                    url=self.start_url,
                    callback=self.parse_anime_detail,
                    meta={"mikan_id": mikan_id, "title": "指定动画"},
                )
            return

        # 根据爬取模式选择解析策略
        if self.mode == "homepage":
            yield from self.parse_homepage(response)
        elif self.mode == "year":
            yield from self.parse_by_year(response, self.year)
        elif self.mode == "season":
            yield from self.parse_by_season(response, self.year, self.season)
        elif self.mode == "full":
            yield from self.parse_full_range(response)
        elif self.mode == "incremental":
            yield from self.parse_incremental(response)
        else:
            self.logger.error(f"未知的爬取模式: {self.mode}")
            yield from self.parse_homepage(response)  # 降级到首页模式

    def parse_homepage(self, response):
        """解析首页，获取动画列表（原有逻辑）"""
        self.logger.info(
            f"开始解析动画列表页面，限制爬取数量: {self.limit if self.limit else '不限制'}"
        )

        # 查找动画链接
        anime_links = response.css('div.m-week-square a[href*="/Home/Bangumi/"]')

        # 根据模式决定是否限制数量
        links_to_process = anime_links[: self.limit] if self.limit else anime_links

        for link in links_to_process:
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

    def parse_by_year(self, response, year):
        """按年份爬取"""
        self.logger.info(f"按年份爬取: {year}年")
        seasons = getattr(self.config, "seasons", ["春", "夏", "秋", "冬"])
        for season in seasons:
            self.logger.info(f"爬取 {year}年{season}季")
            yield from self.parse_by_season(response, year, season)

    def parse_by_season(self, response, year, season):
        """按季度爬取"""
        self.logger.info(f"按季度爬取: {year}年{season}季")

        # 尝试API接口调用
        api_success = yield from self._call_api_or_fallback(year, season)

        if not api_success:
            # API失败，使用动态页面解析
            self.logger.info("API调用失败，使用动态页面解析")
            yield from self._parse_dynamic_page(year, season)

    def parse_full_range(self, response):
        """全量爬取"""
        self.logger.info("开始全量爬取")
        year_range = getattr(self.config, "year_range", {"start": 2013, "end": 2025})
        start_year = year_range["start"]
        end_year = year_range["end"]
        self.logger.info(f"爬取年份范围: {start_year} - {end_year}")
        for year in range(start_year, end_year + 1):
            self.logger.info(f"爬取 {year} 年")
            yield from self.parse_by_year(response, year)

    def parse_incremental(self, response):
        """增量爬取"""
        self.logger.info("开始增量爬取")
        last_crawl_time = getattr(self.config, "last_crawl_time", None)
        if last_crawl_time:
            self.logger.info(f"上次爬取时间: {last_crawl_time}")
            self.logger.info("增量模式暂时使用首页模式")
            yield from self.parse_homepage(response)
        else:
            self.logger.info("首次爬取，使用首页模式")
            yield from self.parse_homepage(response)

    def _call_api_or_fallback(self, year, season):
        """调用API接口或降级处理"""
        api_config = getattr(self.config, "api", {})
        if not api_config.get("enabled", True):
            return False

        # 使用正确的API端点格式
        # URL编码季度名称
        season_encoded = quote(season, encoding="utf-8")
        api_url = f"{self.BASE_URL}/Home/BangumiCoverFlowByDayOfWeek?year={year}&seasonStr={season_encoded}"

        self.logger.info(f"调用API端点: {api_url}")

        try:
            # 使用Scrapy的Request来调用API
            yield Request(
                url=api_url,
                callback=self._parse_api_response,
                meta={"year": year, "season": season, "endpoint": api_url},
                dont_filter=True,
                errback=self._api_error_callback,
            )
            return True

        except Exception as e:
            self.logger.warning(f"API调用失败: {e}")
            return False

    def _parse_api_response(self, response):
        """解析API响应"""
        year = response.meta["year"]
        season = response.meta["season"]
        endpoint = response.meta["endpoint"]

        self.logger.info(f"解析API响应: {endpoint}")

        # 检查响应状态
        if response.status != 200:
            self.logger.warning(f"API响应状态码: {response.status}")
            return

        # 优先尝试解析HTML响应（因为真实API返回HTML）
        content = response.text
        if "/Home/Bangumi/" in content:
            self.logger.info("API返回HTML，提取动画链接")
            yield from self._extract_bangumi_from_html(content, year, season)
            return

        # 尝试解析JSON响应（备用方案）
        try:
            data = response.json()
            if self._contains_bangumi_data(data):
                self.logger.info("成功解析API数据，包含动画信息")
                yield from self._extract_bangumi_from_api(data, year, season)
                return
        except:
            pass

        self.logger.warning(f"无法解析API响应: {endpoint}")

    def _api_error_callback(self, failure):
        """API调用错误回调"""
        self.logger.warning(f"API调用失败: {failure.value}")

    def _parse_dynamic_page(self, year, season):
        """动态页面解析（降级方案）"""
        self.logger.info(f"使用动态页面解析: {year}年{season}季")

        # 这里可以实现Selenium或Playwright的页面交互
        # 暂时返回空，后续实现
        self.logger.info("动态页面解析功能待实现")
        return []

    def _contains_bangumi_data(self, data):
        """检查数据是否包含动画信息"""
        if isinstance(data, dict):
            bangumi_fields = ["bangumi", "anime", "title", "mikan_id", "bangumi_id"]
            for field in bangumi_fields:
                if field in data:
                    return True
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, dict) and self._contains_bangumi_data(item):
                    return True
        return False

    def _extract_bangumi_from_api(self, data, year, season):
        """从API数据中提取动画信息"""
        # 根据API数据结构提取动画ID和标题
        # 这里需要根据实际的API响应格式来实现
        self.logger.info(f"从API数据提取动画信息: {year}年{season}季")

        # 示例实现（需要根据实际API调整）
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    mikan_id = item.get("mikan_id") or item.get("id")
                    title = item.get("title") or item.get("name")
                    if mikan_id:
                        full_url = urljoin(self.BASE_URL, f"/Home/Bangumi/{mikan_id}")
                        yield Request(
                            url=full_url,
                            callback=self.parse_anime_detail,
                            meta={
                                "mikan_id": mikan_id,
                                "title": title or f"{year}年{season}季动画",
                            },
                        )

    def _extract_bangumi_from_html(self, html_content, year, season):
        """从HTML中提取动画信息"""
        # 提取动画详情页链接
        bangumi_links = re.findall(r"/Home/Bangumi/(\d+)", html_content)

        # 提取动画标题
        title_pattern = r'<a[^>]*href="/Home/Bangumi/\d+"[^>]*title="([^"]*)"'
        titles = re.findall(title_pattern, html_content)

        self.logger.info(f"从HTML提取到 {len(bangumi_links)} 个动画")

        # 应用limit限制
        if self.limit:
            bangumi_links = bangumi_links[: self.limit]
            self.logger.info(f"应用limit限制，只处理前 {self.limit} 个动画")

        for i, mikan_id in enumerate(bangumi_links):
            title = titles[i] if i < len(titles) else f"{year}年{season}季动画"
            full_url = urljoin(self.BASE_URL, f"/Home/Bangumi/{mikan_id}")

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
            yield SubtitleGroupItem({
                "id": group["group_id"],
                "name": group["group_name"],
                "created_at": datetime.datetime.now().isoformat(),
            })

        # 提取资源信息
        resources = self._extract_resources(response, mikan_id, subtitle_groups)
        for resource in resources:
            yield ResourceItem({
                "mikan_id": resource["mikan_id"],
                "subtitle_group_id": resource["group_id"],
                "title": resource["title"],
                "file_size": resource["size"],
                "release_date": resource["date"],
                "magnet_url": resource["magnet_link"],
                "magnet_hash": resource["magnet_hash"],
                "torrent_url": resource["torrent_url"],
                "play_url": resource["play_url"],
                "created_at": resource["created_at"],
            })

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
        external_links = response.css('a[href^="http"]::attr(href)').getall()
        # 过滤掉常见的非官方网站
        exclude_domains = ["bgm.tv", "mikanani.me", "bangumi.tv"]
        for link in external_links:
            if not any(domain in link for domain in exclude_domains):
                return link
        return None

    def _find_specific_domains(self, response):
        """查找特定域名的官方网站"""
        specific_domains = [
            "aniplex.co.jp",
            "tbs.co.jp",
            "mbs.jp",
            "tokyo-mx.jp",
            "at-x.com",
            "animax.co.jp",
        ]
        for domain in specific_domains:
            link = response.css(f'a[href*="{domain}"]::attr(href)').get()
            if link:
                return link
        return None

    def _extract_description(self, response):
        """提取描述"""
        # 尝试多种方法提取描述
        description_selectors = [
            ".header2-desc::text",  # 概况介绍部分的描述
            ".bangumi-info p::text",
            ".description::text",
            ".summary::text",
            # 最后才尝试meta description（通常是网站描述，不是动画描述）
            'meta[name="description"]::attr(content)',
        ]

        for selector in description_selectors:
            description = response.css(selector).get()
            if description and len(description.strip()) > 10:
                # 过滤掉网站通用描述
                if "蜜柑计划" not in description and "Mikan Project" not in description:
                    return description.strip()

        return None

    def _extract_subtitle_groups(self, response):
        """提取字幕组信息"""
        subtitle_groups = []

        # 查找所有字幕组div
        group_elements = response.css("div.subgroup-text")

        for element in group_elements:
            group_id = element.attrib.get("id")
            # 提取字幕组名称（第一个链接的文本）
            group_name = element.css("a::text").get()

            if group_id and group_name:
                subtitle_groups.append({
                    "group_id": group_id,
                    "group_name": group_name.strip(),
                })

        self.logger.info(f"提取到 {len(subtitle_groups)} 个字幕组")
        return subtitle_groups

    def _extract_resources(self, response, mikan_id, subtitle_groups):
        """提取资源信息"""
        resources = []

        # 查找所有字幕组div
        group_elements = response.css("div.subgroup-text")

        for group_element in group_elements:
            group_id = group_element.attrib.get("id")
            group_name = group_element.css("a::text").get()

            if not group_id or not group_name:
                continue

            # 查找该字幕组下面的资源表格
            # 字幕组div后面紧跟着的table就是该字幕组的资源表格
            resource_table = group_element.xpath(
                "following-sibling::table[contains(@class, 'table')][1]"
            )

            if resource_table:
                # 提取表格中的所有资源行
                resource_rows = resource_table.css("tbody tr")

                for row in resource_rows:
                    cols = row.css("td")
                    if len(cols) >= 4:  # 确保有足够的列
                        resource = self._parse_resource_row(
                            cols, mikan_id, group_id, group_name.strip()
                        )
                        if resource:
                            resources.append(resource)

        self.logger.info(f"提取到 {len(resources)} 个资源")
        return resources

    def _parse_resource_row(self, cols, mikan_id, group_id, group_name):
        """解析资源行"""
        try:
            # 提取资源信息
            # 第1列：标题（包含磁力链接）
            title_element = cols[0].css("a.magnet-link-wrap")
            title = title_element.css("::text").get() or cols[0].css("::text").get()

            # 第2列：大小
            size = cols[1].css("::text").get()

            # 第3列：更新时间
            date = cols[2].css("::text").get()

            # 第4列：磁力链接（在data-clipboard-text属性中）
            magnet_link = cols[0].css("a.js-magnet::attr(data-clipboard-text)").get()

            # 提取磁力链接的hash值
            magnet_hash = None
            if magnet_link and magnet_link.startswith("magnet:?"):
                import re

                hash_match = re.search(r"xt=urn:btih:([a-fA-F0-9]{40})", magnet_link)
                if hash_match:
                    magnet_hash = hash_match.group(1).lower()

            # 第4列：种子下载链接
            torrent_url = cols[3].css("a::attr(href)").get()
            torrent_url = urljoin(self.BASE_URL, torrent_url) if torrent_url else None

            # 第5列：在线播放链接
            play_url = cols[4].css("a::attr(href)").get()
            play_url = urljoin(self.BASE_URL, play_url) if play_url else None

            if title and magnet_link:
                return {
                    "mikan_id": mikan_id,
                    "group_id": group_id,
                    "group_name": group_name,
                    "title": title.strip(),
                    "size": size.strip() if size else None,
                    "date": date.strip() if date else None,
                    "magnet_link": magnet_link,
                    "magnet_hash": magnet_hash,
                    "torrent_url": torrent_url,
                    "play_url": play_url,
                    "created_at": datetime.datetime.now().isoformat(),
                }
        except Exception as e:
            self.logger.warning(f"解析资源行失败: {e}")

        return None

    def closed(self, reason):
        """爬虫关闭时的处理"""
        self.crawl_log["end_time"] = datetime.datetime.now().isoformat()
        self.crawl_log["status"] = "completed" if reason == "finished" else "failed"
        self.crawl_log["reason"] = reason

        # 记录爬取日志
        self.logger.info(
            f"爬虫结束，状态: {self.crawl_log['status']}, "
            f"模式: {self.crawl_log['crawl_mode']}, "
            f"总资源数: {self.crawl_log['items_count']}"
        )
