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
        >>> extract_episode_number("- 02v2 [WebRip 1080p]")
        2
        >>> extract_episode_number("[07v2] [1080p]")
        7
    """
    if not title:
        return None

    # 按优先级匹配不同的集数格式
    patterns = [
        # 优先匹配明确的集数标识（最可靠）
        r"第(\d{1,4})话",  # 第06话 格式（支持柯南等长篇动画）
        r"第(\d{1,4})集",  # 第06集 格式（支持柯南等长篇动画）
        r"EP(\d{1,3})",  # EP06 格式
        r"E(\d{1,3})",  # E06 格式
        r"Episode\s*(\d{1,3})",  # Episode 06 格式
        # ANi标准格式（带空格或符号分隔，优先级高）
        r"- (\d{1,3})v\d+",  # - 02v2 格式（版本号）
        r"- (\d{1,3})\s",  # - 37 格式
        r"- (\d{1,3})\[",  # - 37[ 格式
        r"- (\d{1,3})\(",  # - 37( 格式
        r"- (\d{1,3})$",  # - 37 结尾格式
        # 版本号格式（优先级高）
        r"\[(\d{1,3})v\d+\]",  # [07v2] 格式（版本号）
        # 其他明确格式
        r"(\d{1,3})话",  # 06话 格式
        r"(\d{1,3})集",  # 06集 格式
        # 方括号格式（优先级最低，需要严格过滤）
        r"\[(\d{1,3})\]",  # [06] 格式（但要排除年份和哈希）
    ]

    for pattern in patterns:
        matches = re.findall(pattern, title, re.IGNORECASE)
        if matches:
            for match in matches:
                episode_num = int(match)
                # 合理性检查：集数通常在1-9999之间（支持长篇动画）
                if 1 <= episode_num <= 9999:
                    # 额外检查：避免误匹配年份、哈希值等
                    if _is_valid_episode_number(title, match, episode_num):
                        return episode_num

    return None


def _is_valid_episode_number(title: str, matched_str: str, episode_num: int) -> bool:
    """
    验证解析出的集数是否合理

    Args:
        title: 完整标题
        matched_str: 匹配到的数字字符串
        episode_num: 解析出的集数

    Returns:
        是否为有效的集数
    """
    # 排除明显的年份（2000-2030）
    if 2000 <= episode_num <= 2030:
        return False

        # 排除可能的哈希值（通常在标题末尾，且包含字母数字混合）
    # 检查是否在包含字母的方括号内（如 [7D1E7858]）
    hash_brackets = re.findall(r"\[([A-Fa-f0-9]+)\]", title)
    for hash_candidate in hash_brackets:
        # 如果方括号内容包含字母且长度>=6，很可能是哈希值
        if len(hash_candidate) >= 6 and re.search(
            r"[A-Fa-f]", hash_candidate, re.IGNORECASE
        ):
            if matched_str in hash_candidate:
                return False

    # 排除范围格式（如 [01-12]）
    range_pattern = (
        rf"\[\d+-{re.escape(matched_str)}\]|\[{re.escape(matched_str)}-\d+\]"
    )
    if re.search(range_pattern, title):
        return False

    return True


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
        >>> extract_resolution("(CR 1920x1080 AVC AAC MKV)")
        "1080p"
        >>> extract_resolution("[HDTV][x264 AAC]")
        "720p"
        >>> extract_resolution("[WebRip][HEVC_AAC]")
        "1080p"
    """
    if not title:
        return None

    # 匹配常见分辨率格式 - 按优先级排序
    patterns = [
        # 优先匹配明确的p格式
        (r"(\d{3,4}[pP])", lambda m: m.group(1).lower()),  # 1080p, 720p, 480p等
        # 从分辨率尺寸推断格式（支持大小写x，支持3-4位宽度）
        (
            r"(\d{3,4})[xX](\d{3,4})",
            lambda m: _resolution_from_dimensions(m.group(1), m.group(2)),
        ),
        # 匹配隔行扫描格式
        (r"(\d{3,4}[iI])", lambda m: m.group(1).lower()),  # 1080i, 720i等
        # 匹配K格式
        (r"(\d{1,2}K)", lambda m: m.group(1).upper()),  # 4K, 8K等
    ]

    for pattern, converter in patterns:
        match = re.search(pattern, title)
        if match:
            resolution = converter(match)
            if resolution:
                return resolution

    # 如果直接匹配失败，尝试从视频源和编码格式推断
    return _infer_resolution_from_source_and_codec(title)


def _resolution_from_dimensions(width: str, height: str) -> Optional[str]:
    """
    从宽高尺寸推断分辨率标准

    Args:
        width: 宽度（如"1920"）
        height: 高度（如"1080"）

    Returns:
        标准分辨率字符串或None
    """
    try:
        w, h = int(width), int(height)

        # 常见分辨率映射
        resolution_map = {
            (3840, 2160): "2160p",  # 4K
            (2560, 1440): "1440p",  # 2K
            (1920, 1080): "1080p",  # Full HD
            (1280, 720): "720p",  # HD
            (854, 480): "480p",  # SD
            (640, 480): "480p",  # SD
            (426, 240): "240p",  # Low quality
        }

        # 直接匹配
        if (w, h) in resolution_map:
            return resolution_map[(w, h)]

        # 根据高度推断（常见做法）
        if h >= 2100:
            return "2160p"
        elif h >= 1400:
            return "1440p"
        elif h >= 1070:
            return "1080p"
        elif h >= 700:
            return "720p"
        elif h >= 470:
            return "480p"
        else:
            return "240p"

    except ValueError:
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
        >>> extract_subtitle_type("[简繁内挂]")
        "简繁内挂"
    """
    if not title:
        return None

    # 常见字幕类型关键词（按优先级排序）
    subtitle_keywords = [
        # 多语言内封组合（最高优先级，长词优先）
        "简繁日内封",  # 三语内封
        "简繁日内嵌",  # 三语内嵌
        "简繁日多语",  # 三语多语
        "简繁英",  # 简繁英多语
        # 双语相关（优先级高，长词优先）
        "简体日语双语",  # 详细描述
        "繁体日语双语",  # 详细描述
        "简日双语",  # 简体中文+日语双语
        "简日双字",
        "繁日双语",  # 繁体中文+日语双语
        "繁日双字",
        "中日双语",  # 中文+日语双语
        "中日双字",
        "简繁双语",  # 简繁体双语
        "简繁双字",
        "双语字幕",  # 通用双语
        "简日",
        "繁日",
        "简英",
        "繁英",
        "简繁",
        # 内封/内嵌相关（按语言分类）
        "简日内封",  # 简体日语内封
        "繁日内封",  # 繁体日语内封
        "简日内嵌",  # 简体日语内嵌
        "繁日内嵌",  # 繁体日语内嵌
        "简繁内封",  # 简繁体内封
        "简繁内挂",  # 简繁体内挂
        "简繁内嵌",  # 简繁体内嵌
        "简体内封",  # 简体内封
        "简体内挂",  # 简体内挂
        "简体内嵌",  # 简体内嵌
        "繁体内封",  # 繁体内封
        "繁体内挂",  # 繁体内挂
        "繁体内嵌",  # 繁体内嵌
        # 外挂字幕
        "简体外挂",  # 简体外挂
        "繁体外挂",  # 繁体外挂
        "简繁外挂",  # 简繁外挂
        "外挂字幕",  # 通用外挂
        # 语言标记（缩写）- 优先级提高
        "CHT",  # 繁体中文标记
        "CHS",  # 简体中文标记
        "GB",  # 国标简体
        "BIG5",  # 繁体编码
        # 特殊标记（优先级提高）
        "简体",  # 简体标记
        "繁体",  # 繁体标记
        "简中",  # 简体中文缩写
        "繁中",  # 繁体中文缩写
        "中字",  # 中文字幕缩写
        "英语",  # 英语字幕缩写
        # 通用字幕描述（优先级降低）
        "内嵌字幕",  # 通用内嵌
        "内挂字幕",  # 通用内挂
        "中文字幕",  # 中文字幕
        # 其他
        "日语原声",  # 日语原声
        "无字幕",  # 无字幕
        "RAW",  # 生肉
    ]

    # 按优先级检查
    for keyword in subtitle_keywords:
        if keyword in title:
            return keyword

    return "其他"


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
    """
    return datetime.fromtimestamp(timestamp).isoformat()


def get_current_timestamp() -> int:
    """
    获取当前Unix时间戳

    Returns:
        当前Unix时间戳（整数）
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
    common_resolutions = ["240p", "480p", "720p", "1080p", "1440p", "2160p", "4K", "8K"]
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


def _infer_resolution_from_source_and_codec(title: str) -> Optional[str]:
    """
    从视频源标识和编码格式推断分辨率

    Args:
        title: 资源标题

    Returns:
        推断的分辨率字符串或None
    """
    title_upper = title.upper()

    # 视频源分辨率推断规则（按优先级排序）
    source_resolution_map = [
        # 高分辨率源
        ("BDRIP", "1080p"),  # 蓝光抓取通常是1080p
        ("BLURAY", "1080p"),  # 蓝光源
        ("BD", "1080p"),  # 蓝光缩写
        ("WEBRIP", "1080p"),  # Web抓取通常是1080p
        ("WEB-DL", "1080p"),  # Web下载
        ("WEBDL", "1080p"),  # Web下载变体
        # 中等分辨率源
        ("HDTV", "720p"),  # 高清电视通常是720p
        ("HDTVRIP", "720p"),  # 高清电视抓取
        # 低分辨率源
        ("DVDRIP", "480p"),  # DVD抓取
        ("DVD", "480p"),  # DVD源
        ("TVRIP", "480p"),  # 电视抓取
        ("SDTV", "480p"),  # 标清电视
    ]

    # 检查视频源标识
    for source, resolution in source_resolution_map:
        if source in title_upper:
            # 如果有HEVC编码且是720p源，可能升级到1080p
            if resolution == "720p" and (
                "HEVC" in title_upper or "H.265" in title_upper
            ):
                return "1080p"
            return resolution

    # 从编码格式推断（最后的备选方案）
    if "HEVC" in title_upper or "H.265" in title_upper:
        return "1080p"  # HEVC通常用于高分辨率
    elif "H.264" in title_upper or "X264" in title_upper or "AVC" in title_upper:
        return "720p"  # H.264可能是720p（保守估计）

    return None


def normalize_subtitle_type(subtitle_type: str) -> Optional[str]:
    """
    将细分的字幕类型标准化为精简的核心类型

    Args:
        subtitle_type: 原始解析的字幕类型

    Returns:
        标准化后的字幕类型，未识别返回None

    Examples:
        >>> normalize_subtitle_type("简日双语")
        "中日双语"
        >>> normalize_subtitle_type("CHT")
        "繁体中文"
        >>> normalize_subtitle_type("简繁日内封")
        "简繁双语"
    """
    if not subtitle_type:
        return None

    # 字幕类型标准化映射表
    normalization_map = {
        # 中日双语类（最高优先级）
        "简日双语": "中日双语",
        "繁日双语": "中日双语",
        "中日双语": "中日双语",
        "简日双字": "中日双语",
        "繁日双字": "中日双语",
        "中日双字": "中日双语",
        "简日": "中日双语",
        "繁日": "中日双语",
        "简体日语双语": "中日双语",
        "繁体日语双语": "中日双语",
        # 简繁双语类
        "简繁": "简繁双语",
        "简繁双语": "简繁双语",
        "简繁双字": "简繁双语",
        "简繁日内封": "简繁日",
        "简繁日内嵌": "简繁日",
        "简繁日多语": "简繁日",
        "简繁英": "简繁英",
        "简繁外挂": "简繁双语",
        # 简体中文类
        "CHS": "简体中文",
        "简体": "简体中文",
        "简中": "简体中文",
        "GB": "简体中文",
        "简体内嵌": "简体中文",
        "简体内封": "简体中文",
        "简体内挂": "简体中文",
        "简体外挂": "简体中文",
        "简英": "简体中文",
        # 繁体中文类
        "CHT": "繁体中文",
        "繁体": "繁体中文",
        "繁中": "繁体中文",
        "BIG5": "繁体中文",
        "繁体内嵌": "繁体中文",
        "繁体内封": "繁体中文",
        "繁体内挂": "繁体中文",
        "繁体外挂": "繁体中文",
        "繁英": "繁体中文",
        # 多语字幕类
        "英语": "英语",
        "双语字幕": "多语字幕",
        # 中文字幕类（通用）
        "中字": "中文字幕",
        "中文字幕": "中文字幕",
        "内嵌字幕": "中文字幕",
        "内挂字幕": "中文字幕",
        "外挂字幕": "中文字幕",
        # 无字幕类
        "无字幕": "无字幕",
        "RAW": "无字幕",
        "日语原声": "无字幕",
    }

    return normalization_map.get(subtitle_type, "其他")


if __name__ == "__main__":
    # 测试示例
    test_titles = [
        "[芝士动物朋友] 石纪元 科学与未来 [06][CR-WebRip][1080p][HEVC+AAC][简繁内封]（新石纪 第四季 S4）",
        "[LoliHouse] 药屋少女的呢喃 第二季 / Kusuriya no Hitorigoto S2 [12][WebRip 1080p HEVC-10bit AAC][简繁内封字幕]",
        "名侦探柯南 第1147话 [720p]",
        "某动画 EP05 中日双语 [480p]",
        "[黒ネズミたち] 这是妳与我的最后战场 - 11 (CR 1920x1080 AVC AAC MKV)",
        "[Prejudice-Studio] 某动画 - 11 [Bilibili WEB-DL 1080P AVC 8bit AAC MP4][简繁内挂]",
    ]

    print("=== 优化后的文本解析测试 ===")
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
