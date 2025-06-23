#!/usr/bin/env python3
"""
文本解析工具模块
用于从动漫资源标题中提取结构化信息
"""

import re
import time
from datetime import datetime
from typing import Optional


def extract_episode_number(title: str) -> Optional[int]:
    """
    从资源标题中提取集数

    Args:
        title: 资源标题，如 "[芝士动物朋友] 石纪元 科学与未来 [06][CR-WebRip][1080p]"

    Returns:
        集数（整数），如果未找到则返回None

    Examples:
        >>> extract_episode_number("[芝士动物朋友] 石纪元 科学与未来 [06][CR-WebRip][1080p]")
        6
        >>> extract_episode_number("某动画 第12话 [1080p]")
        12
        >>> extract_episode_number("某动画 EP05 [720p]")
        5
    """
    if not title:
        return None

    # 按优先级匹配不同的集数格式
    patterns = [
        r"\[(\d{1,4})\]",  # [06] 或 [1147] 格式 - 最常见
        r"第(\d{1,4})话",  # 第06话 或 第1147话 格式
        r"第(\d{1,4})集",  # 第06集 格式
        r"EP(\d{1,4})",  # EP06 格式
        r"E(\d{1,4})",  # E06 格式
        r"Episode\s*(\d{1,4})",  # Episode 06 格式
        r"- (\d{1,4})\s",  # - 37 格式（ANi标准）
        r"- (\d{1,4})\[",  # - 37[ 格式
        r"(\d{1,4})话",  # 06话 格式
        r"(\d{1,4})集",  # 06集 格式
    ]

    for pattern in patterns:
        match = re.search(pattern, title, re.IGNORECASE)
        if match:
            episode_num = int(match.group(1))
            # 合理性检查：集数通常在1-9999之间
            if 1 <= episode_num <= 9999:
                return episode_num

    return None


def extract_resolution(title: str) -> Optional[str]:
    """
    从资源标题中提取分辨率信息

    Args:
        title: 资源标题

    Returns:
        分辨率字符串，如 "1080p", "720p"，未找到返回None

    Examples:
        >>> extract_resolution("[芝士动物朋友] 石纪元 [06][1080p][HEVC+AAC]")
        "1080p"
        >>> extract_resolution("某动画 [720P] [简繁内封]")
        "720p"
    """
    if not title:
        return None

    # 匹配常见分辨率格式
    patterns = [
        r"(\d{3,4}[pP])",  # 1080p, 720p, 480p等
        r"(\d{3,4}[iI])",  # 1080i, 720i等隔行扫描
        r"(\d{1,2}K)",  # 4K, 8K等
    ]

    for pattern in patterns:
        match = re.search(pattern, title)
        if match:
            resolution = match.group(1).lower()
            # 标准化格式：统一为小写
            if resolution.endswith("i"):
                resolution = resolution[:-1] + "i"
            elif resolution.endswith("p"):
                resolution = resolution[:-1] + "p"
            elif resolution.endswith("k"):
                resolution = resolution[:-1] + "K"  # K保持大写
            return resolution

    return None


def extract_subtitle_type(title: str) -> Optional[str]:
    """
    从资源标题中提取字幕类型信息

    Args:
        title: 资源标题

    Returns:
        字幕类型字符串，未找到返回None

    Examples:
        >>> extract_subtitle_type("[芝士动物朋友] 石纪元 [06][简繁内封]")
        "简繁内封"
        >>> extract_subtitle_type("某动画 [中日双语] [1080p]")
        "中日双语"
    """
    if not title:
        return None

    # 常见字幕类型关键词（按优先级排序）
    subtitle_keywords = [
        "简繁内封",
        "中日双语",
        "简体内封",
        "繁体内封",
        "简繁双语",
        "中文字幕",
        "日语原声",
        "内嵌字幕",
        "外挂字幕",
        "双语字幕",
        "CHT",  # 繁体中文标记
        "CHS",  # 简体中文标记
        "无字幕",
        "RAW",
    ]

    # 按优先级检查
    for keyword in subtitle_keywords:
        if keyword in title:
            return keyword

    return None


def parse_datetime_to_timestamp(datetime_str: str) -> Optional[int]:
    """
    将各种时间字符串格式转换为Unix时间戳

    Args:
        datetime_str: 时间字符串，支持多种格式

    Returns:
        Unix时间戳（整数），解析失败返回None

    Examples:
        >>> parse_datetime_to_timestamp("2025-06-20T17:49:57.252831")
        1750454997
        >>> parse_datetime_to_timestamp("2025-06-20 17:49:57")
        1750454997
    """
    if not datetime_str:
        return None

    # 支持的时间格式（按优先级排序）
    formats = [
        "%Y/%m/%d %H:%M",  # Mikan格式：2025/06/23 13:50
        "%m/%d/%Y",  # Mikan放送日期：10/7/2024
        "%Y-%m-%dT%H:%M:%S.%f",  # ISO格式带微秒
        "%Y-%m-%dT%H:%M:%S",  # ISO格式不带微秒
        "%Y-%m-%d %H:%M:%S",  # 标准格式
        "%Y-%m-%d %H:%M",  # 不带秒
        "%Y-%m-%d",  # 只有日期
        "%Y/%m/%d %H:%M:%S",  # 完整斜杠格式
        "%Y/%m/%d",  # 年/月/日格式
        "%m/%d/%Y %H:%M:%S",  # 美式格式
        "%d/%m/%Y %H:%M:%S",  # 欧式格式
        "%m/%d/%Y %H:%M",  # 美式格式不带秒
        "%d/%m/%Y %H:%M",  # 欧式格式不带秒
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(datetime_str.strip(), fmt)
            return int(dt.timestamp())
        except ValueError:
            continue

    return None


def timestamp_to_datetime(timestamp: int) -> str:
    """
    将Unix时间戳转换为ISO格式时间字符串

    Args:
        timestamp: Unix时间戳

    Returns:
        ISO格式时间字符串

    Examples:
        >>> timestamp_to_datetime(1750454997)
        "2025-06-20T17:49:57"
    """
    try:
        dt = datetime.fromtimestamp(timestamp)
        return dt.isoformat()
    except (ValueError, OSError):
        return datetime.now().isoformat()


def get_current_timestamp() -> int:
    """
    获取当前Unix时间戳

    Returns:
        当前Unix时间戳
    """
    return int(time.time())


def validate_parsed_data(
    title: str,
    episode_number: Optional[int],
    resolution: Optional[str],
    subtitle_type: Optional[str],
) -> dict:
    """
    验证解析结果的合理性并返回统计信息

    Args:
        title: 原始标题
        episode_number: 解析的集数
        resolution: 解析的分辨率
        subtitle_type: 解析的字幕类型

    Returns:
        包含验证结果和统计信息的字典
    """
    result = {"is_valid": True, "warnings": [], "confidence": 1.0}

    # 集数合理性检查
    if episode_number is not None:
        if episode_number < 1 or episode_number > 9999:
            result["warnings"].append(f"集数 {episode_number} 超出合理范围")
            result["confidence"] *= 0.7

    # 分辨率合理性检查
    common_resolutions = ["480p", "720p", "1080p", "1440p", "2160p", "4K", "8K"]
    if resolution and resolution not in common_resolutions:
        result["warnings"].append(f"分辨率 {resolution} 不常见")
        result["confidence"] *= 0.9

    # 标题长度检查
    if len(title) < 10:
        result["warnings"].append("标题过短，可能解析不准确")
        result["confidence"] *= 0.8

    if result["confidence"] < 0.6:
        result["is_valid"] = False

    return result


if __name__ == "__main__":
    # 测试示例
    test_titles = [
        "[芝士动物朋友] 石纪元 科学与未来 [06][CR-WebRip][1080p][HEVC+AAC][简繁内封]（新石纪 第四季 S4）",
        "[LoliHouse] 药屋少女的呢喃 第二季 / Kusuriya no Hitorigoto S2 [12][WebRip 1080p HEVC-10bit AAC][简繁内封字幕]",
        "名侦探柯南 第1147话 [720p]",
        "某动画 EP05 中日双语 [480p]",
    ]

    print("=== 文本解析测试 ===")
    for title in test_titles:
        print(f"\n标题: {title}")
        episode = extract_episode_number(title)
        resolution = extract_resolution(title)
        subtitle_type = extract_subtitle_type(title)

        print(f"集数: {episode}")
        print(f"分辨率: {resolution}")
        print(f"字幕类型: {subtitle_type}")

        validation = validate_parsed_data(title, episode, resolution, subtitle_type)
        print(f"验证: {validation}")
