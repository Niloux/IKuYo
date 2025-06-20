"""
动态页面解析中间件
用于在API接口不可用时，使用浏览器自动化工具进行页面交互
"""

import time

from scrapy import signals
from scrapy.http import HtmlResponse


class DynamicParserMiddleware:
    """动态页面解析中间件"""

    def __init__(self, crawler):
        self.crawler = crawler
        self.driver = None
        self.enabled = crawler.settings.getbool("DYNAMIC_PARSER_ENABLED", True)
        self.wait_time = crawler.settings.getint("DYNAMIC_PARSER_WAIT_TIME", 3)
        self.timeout = crawler.settings.getint("DYNAMIC_PARSER_TIMEOUT", 60)

        # 注册信号
        crawler.signals.connect(self.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(self.spider_closed, signal=signals.spider_closed)

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    def spider_opened(self, spider):
        """爬虫开始时初始化浏览器"""
        if self.enabled and hasattr(spider, "mode") and spider.mode in ["year", "season", "full"]:
            spider.logger.info("初始化动态页面解析中间件")
            self._init_browser()

    def spider_closed(self, spider):
        """爬虫结束时关闭浏览器"""
        if self.driver:
            spider.logger.info("关闭浏览器")
            self._close_browser()

    def _init_browser(self):
        """初始化浏览器"""
        try:
            # 尝试导入Selenium
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.webdriver.support.ui import WebDriverWait

            # 配置Chrome选项
            chrome_options = Options()
            chrome_options.add_argument("--headless")  # 无头模式
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")

            # 设置用户代理
            chrome_options.add_argument(
                "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            )

            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.set_page_load_timeout(self.timeout)

            # 保存导入的模块供后续使用
            self.webdriver = webdriver
            self.By = By
            self.WebDriverWait = WebDriverWait
            self.EC = EC

            return True

        except ImportError:
            print("Selenium未安装，动态解析功能不可用")
            self.driver = None
            return False
        except Exception as e:
            print(f"初始化浏览器失败: {e}")
            self.driver = None
            return False

    def _close_browser(self):
        """关闭浏览器"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            finally:
                self.driver = None

    def process_request(self, request, spider):
        """处理请求"""
        # 检查是否需要动态解析
        if not self._should_use_dynamic_parser(request, spider):
            return None

        # 检查浏览器是否可用
        if not self.driver:
            spider.logger.warning("浏览器未初始化，跳过动态解析")
            return None

        try:
            # 执行动态页面解析
            html_content = self._parse_dynamic_page(request, spider)
            if html_content:
                # 返回HtmlResponse
                return HtmlResponse(
                    url=request.url,
                    body=html_content.encode("utf-8"),
                    encoding="utf-8",
                    request=request,
                )
        except Exception as e:
            spider.logger.error(f"动态页面解析失败: {e}")

        return None

    def _should_use_dynamic_parser(self, request, spider):
        """判断是否应该使用动态解析"""
        # 检查是否为年份或季度爬取模式
        if not hasattr(spider, "mode") or spider.mode not in ["year", "season", "full"]:
            return False

        # 检查URL是否包含年份和季度信息
        url = request.url
        if "/Home/Bangumi/" in url and ("year=" in url or hasattr(spider, "year") and spider.year):
            return True

        return False

    def _parse_dynamic_page(self, request, spider):
        """执行动态页面解析"""
        spider.logger.info(f"开始动态页面解析: {request.url}")

        try:
            # 访问首页
            if self.driver:
                self.driver.get("https://mikanani.me/Home")
                time.sleep(self.wait_time)

                # 根据爬取模式执行不同的操作
                if spider.mode == "year":
                    return self._parse_by_year(spider.year, spider)
                elif spider.mode == "season":
                    return self._parse_by_season(spider.year, spider.season, spider)
                elif spider.mode == "full":
                    return self._parse_full_range(spider)
                else:
                    return None

        except Exception as e:
            spider.logger.error(f"动态页面解析异常: {e}")
            return None

    def _parse_by_year(self, year, spider):
        """按年份解析"""
        spider.logger.info(f"动态解析 {year} 年")

        seasons = ["春", "夏", "秋", "冬"]
        all_content = []

        for season in seasons:
            try:
                content = self._parse_by_season(year, season, spider)
                if content:
                    all_content.append(content)
            except Exception as e:
                spider.logger.warning(f"解析 {year}年{season}季 失败: {e}")

        # 合并所有内容
        if all_content:
            return "\n".join(all_content)

        return None

    def _parse_by_season(self, year, season, spider):
        """按季度解析"""
        spider.logger.info(f"动态解析 {year}年{season}季")

        try:
            if not self.driver:
                return None

            # 查找并点击年份和季度链接
            season_clicked = self._click_season_link(year, season)
            if not season_clicked:
                spider.logger.warning(f"未找到 {year}年{season}季 的链接")
                return None

            # 等待页面加载
            time.sleep(self.wait_time)

            # 提取动画链接
            anime_links = self._extract_anime_links()
            spider.logger.info(f"找到 {len(anime_links)} 个动画链接")

            # 访问每个动画详情页并提取内容
            all_content = []
            for link in anime_links:
                try:
                    content = self._extract_anime_content(link)
                    if content:
                        all_content.append(content)
                except Exception as e:
                    spider.logger.warning(f"提取动画内容失败: {e}")

            return "\n".join(all_content)

        except Exception as e:
            spider.logger.error(f"解析 {year}年{season}季 异常: {e}")
            return None

    def _parse_full_range(self, spider):
        """全量解析"""
        spider.logger.info("开始全量动态解析")

        year_range = getattr(spider, "year_range", {"start": 2013, "end": 2025})
        start_year = year_range["start"]
        end_year = year_range["end"]

        all_content = []

        for year in range(start_year, end_year + 1):
            try:
                content = self._parse_by_year(year, spider)
                if content:
                    all_content.append(content)
            except Exception as e:
                spider.logger.warning(f"解析 {year} 年失败: {e}")

        return "\n".join(all_content) if all_content else None

    def _click_season_link(self, year, season):
        """点击年份和季度链接"""
        try:
            if not self.driver or not hasattr(self, "By"):
                return False

            # 查找包含年份和季度信息的链接
            season_links = self.driver.find_elements(
                self.By.XPATH, f"//a[@data-year='{year}' and @data-season='{season}']"
            )

            if season_links:
                season_links[0].click()
                return True

            # 备用方法：查找包含年份和季度文本的链接
            season_text = f"{year}年{season}季"
            season_links = self.driver.find_elements(
                self.By.XPATH, f"//a[contains(text(), '{season_text}')]"
            )

            if season_links:
                season_links[0].click()
                return True

            return False

        except Exception as e:
            print(f"点击季度链接失败: {e}")
            return False

    def _extract_anime_links(self):
        """提取动画链接"""
        try:
            if not self.driver or not hasattr(self, "By"):
                return []

            # 查找动画详情页链接
            anime_links = self.driver.find_elements(
                self.By.XPATH, "//a[contains(@href, '/Home/Bangumi/')]"
            )

            links = []
            for link in anime_links:
                href = link.get_attribute("href")
                if href and "/Home/Bangumi/" in href:
                    links.append(href)

            return links

        except Exception as e:
            print(f"提取动画链接失败: {e}")
            return []

    def _extract_anime_content(self, anime_url):
        """提取动画详情页内容"""
        try:
            if not self.driver:
                return None

            # 访问动画详情页
            self.driver.get(anime_url)
            time.sleep(self.wait_time)

            # 获取页面内容
            page_source = self.driver.page_source

            # 提取动画信息
            anime_info = self._parse_anime_page(page_source)

            return anime_info

        except Exception as e:
            print(f"提取动画内容失败: {e}")
            return None

    def _parse_anime_page(self, html_content):
        """解析动画页面HTML"""
        try:
            # 这里可以实现具体的HTML解析逻辑
            # 暂时返回原始HTML，让Scrapy的解析器处理
            return html_content

        except Exception as e:
            print(f"解析动画页面失败: {e}")
            return None


class DynamicParserDownloaderMiddleware:
    """动态解析下载器中间件"""

    def __init__(self, crawler):
        self.crawler = crawler
        self.dynamic_parser = DynamicParserMiddleware(crawler)

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    def process_request(self, request, spider):
        """处理下载请求"""
        return self.dynamic_parser.process_request(request, spider)

    def process_response(self, request, response, spider):
        """处理响应"""
        # 如果响应状态码不是200，尝试动态解析
        if response.status != 200:
            spider.logger.warning(f"响应状态码 {response.status}: {response.url}")

            # 检查是否应该使用动态解析
            if self.dynamic_parser._should_use_dynamic_parser(request, spider):
                spider.logger.info("尝试使用动态解析")
                dynamic_response = self.dynamic_parser.process_request(request, spider)
                if dynamic_response:
                    return dynamic_response

        return response

    def process_exception(self, request, exception, spider):
        """处理异常"""
        # 如果请求失败，尝试动态解析
        spider.logger.warning(f"请求失败: {exception}")

        # 检查是否应该使用动态解析
        if self.dynamic_parser._should_use_dynamic_parser(request, spider):
            spider.logger.info("请求失败，尝试使用动态解析")
            dynamic_response = self.dynamic_parser.process_request(request, spider)
            if dynamic_response:
                return dynamic_response

        return None
