"""
Mikan Project API接口分析工具
用于分析UpdateBangumiCoverFlow函数的网络请求和API接口
"""

import json
import re
from typing import Dict, List, Optional, Union
from urllib.parse import parse_qs, urljoin, urlparse

import requests


class MikanAPIAnalyzer:
    """Mikan Project API接口分析器"""

    def __init__(self, base_url: str = "https://mikanani.me"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        })

    def analyze_update_bangumi_flow(self, year: int, season: str) -> Dict:
        """
        分析UpdateBangumiCoverFlow函数的API调用

        Args:
            year: 年份
            season: 季度（春、夏、秋、冬）

        Returns:
            API调用信息字典
        """
        # 根据HTML分析，UpdateBangumiCoverFlow函数可能的API端点
        possible_endpoints = [
            f"/Home/Bangumi/{year}/{season}",
            f"/Home/Bangumi?year={year}&season={season}",
            f"/api/bangumi?year={year}&season={season}",
            f"/Home/GetBangumiList?year={year}&season={season}",
        ]

        api_info = {
            "year": year,
            "season": season,
            "endpoints": [],
            "successful_endpoint": None,
            "response_data": None,
            "error": None,
        }

        for endpoint in possible_endpoints:
            try:
                url = urljoin(self.base_url, endpoint)
                response = self.session.get(url, timeout=10)

                api_info["endpoints"].append({
                    "url": url,
                    "status_code": response.status_code,
                    "content_type": response.headers.get("content-type", ""),
                    "content_length": len(response.content),
                })

                # 检查响应是否包含动画数据
                if self._is_valid_bangumi_response(response):
                    api_info["successful_endpoint"] = url
                    api_info["response_data"] = self._parse_response_data(response)
                    break

            except Exception as e:
                api_info["endpoints"].append({"url": url, "error": str(e)})

        return api_info

    def _is_valid_bangumi_response(self, response: requests.Response) -> bool:
        """检查响应是否包含有效的动画数据"""
        if response.status_code != 200:
            return False

        content_type = response.headers.get("content-type", "")

        # 检查是否为JSON响应
        if "application/json" in content_type:
            try:
                data = response.json()
                # 检查是否包含动画相关字段
                return self._contains_bangumi_data(data)
            except:
                return False

        # 检查是否为HTML响应且包含动画链接
        if "text/html" in content_type:
            content = response.text
            # 检查是否包含动画详情页链接
            return "/Home/Bangumi/" in content

        return False

    def _contains_bangumi_data(self, data: Union[Dict, List]) -> bool:
        """检查数据是否包含动画信息"""
        # 检查常见的动画数据字段
        bangumi_fields = ["bangumi", "anime", "title", "mikan_id", "bangumi_id"]

        if isinstance(data, dict):
            # 检查顶层字段
            for field in bangumi_fields:
                if field in data:
                    return True

            # 递归检查嵌套字段
            for value in data.values():
                if isinstance(value, (dict, list)):
                    if self._contains_bangumi_data(value):
                        return True

        elif isinstance(data, list):
            # 检查列表中的每个元素
            for item in data:
                if isinstance(item, dict) and self._contains_bangumi_data(item):
                    return True

        return False

    def _parse_response_data(self, response: requests.Response) -> Optional[Dict]:
        """解析响应数据"""
        content_type = response.headers.get("content-type", "")

        if "application/json" in content_type:
            try:
                return response.json()
            except:
                return None

        elif "text/html" in content_type:
            # 解析HTML中的动画链接
            return self._extract_bangumi_links_from_html(response.text)

        return None

    def _extract_bangumi_links_from_html(self, html_content: str) -> Dict:
        """从HTML中提取动画链接"""

        # 提取动画详情页链接
        bangumi_links = re.findall(r"/Home/Bangumi/(\d+)", html_content)

        # 提取动画标题
        title_pattern = r'<a[^>]*href="/Home/Bangumi/\d+"[^>]*title="([^"]*)"'
        titles = re.findall(title_pattern, html_content)

        return {
            "type": "html",
            "bangumi_count": len(bangumi_links),
            "bangumi_ids": list(set(bangumi_links)),  # 去重
            "titles": titles[: len(bangumi_links)],  # 对应标题
        }

    def generate_api_template(self, year: int, season: str) -> Dict:
        """生成API调用模板"""
        api_info = self.analyze_update_bangumi_flow(year, season)

        template = {
            "year": year,
            "season": season,
            "api_endpoint": api_info.get("successful_endpoint"),
            "method": "GET",
            "headers": {
                "User-Agent": self.session.headers.get("User-Agent"),
                "Accept": "application/json, text/html, */*",
                "Referer": f"{self.base_url}/Home",
            },
            "params": {},
            "example_usage": None,
        }

        if api_info.get("successful_endpoint"):
            # 解析URL参数
            parsed_url = urlparse(api_info["successful_endpoint"])
            if parsed_url.query:
                template["params"] = parse_qs(parsed_url.query)

            # 生成使用示例
            template["example_usage"] = f"""
# Python requests示例
import requests

url = "{api_info["successful_endpoint"]}"
headers = {json.dumps(template["headers"], indent=2, ensure_ascii=False)}

response = requests.get(url, headers=headers)
if response.status_code == 200:
    data = response.json()  # 或 response.text
    print(f"成功获取{year}年{season}季动画数据")
"""

        return template

    def test_all_seasons(self, year: int) -> Dict:
        """测试指定年份的所有季度"""
        results = {}
        seasons = ["春", "夏", "秋", "冬"]

        for season in seasons:
            results[season] = self.analyze_update_bangumi_flow(year, season)

        return results

    def find_working_api(self, year: int = 2024) -> Optional[str]:
        """查找可用的API端点"""
        seasons = ["春", "夏", "秋", "冬"]

        for season in seasons:
            api_info = self.analyze_update_bangumi_flow(year, season)
            if api_info.get("successful_endpoint"):
                return api_info["successful_endpoint"]

        return None


def analyze_mikan_api():
    """分析Mikan API的主函数"""
    analyzer = MikanAPIAnalyzer()

    print("开始分析Mikan Project API接口...")

    # 测试2024年的所有季度
    test_year = 2024
    results = analyzer.test_all_seasons(test_year)

    print(f"\n{test_year}年各季度API测试结果:")
    for season, result in results.items():
        print(f"\n{season}季:")
        if result.get("successful_endpoint"):
            print(f"  ✅ 成功: {result['successful_endpoint']}")
            if result.get("response_data"):
                data = result["response_data"]
                if isinstance(data, dict) and "bangumi_count" in data:
                    print(f"  📊 动画数量: {data['bangumi_count']}")
        else:
            print("  ❌ 失败: 未找到可用端点")
            for endpoint_info in result.get("endpoints", []):
                if "error" in endpoint_info:
                    print(f"    - {endpoint_info['url']}: {endpoint_info['error']}")

    # 查找可用的API端点
    working_api = analyzer.find_working_api()
    if working_api:
        print(f"\n🎉 找到可用API端点: {working_api}")

        # 生成API模板
        template = analyzer.generate_api_template(2024, "春")
        print("\n📋 API调用模板:")
        print(json.dumps(template, indent=2, ensure_ascii=False))
    else:
        print("\n❌ 未找到可用的API端点，可能需要使用动态页面解析")


if __name__ == "__main__":
    analyze_mikan_api()
