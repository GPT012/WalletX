#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BIP-39官方词汇表管理模块

该模块从官方bitcoin/bips仓库的BIP-39词表文件加载标准词汇。
专注于英文支持，确保助记词生成和验证的准确性和稳定性。

Author: AI Assistant
Date: 2024
"""

import os
from typing import Dict, List, Optional


class WordlistManager:
    """
    BIP-39官方词汇表管理器

    从官方BIP-39词表文件加载和管理标准词汇表，提供词汇验证、搜索和信息查询功能。
    """

    def __init__(self):
        """初始化词汇表管理器"""
        self._english_wordlist = self._load_english_wordlist()

    def _load_english_wordlist(self) -> List[str]:
        """从官方BIP-39英语词表文件加载词汇表"""
        # 获取当前文件的目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # 构建BIP39词表文件路径
        wordlist_path = os.path.join(current_dir, "..", "bip39", "english.txt")

        try:
            with open(wordlist_path, "r", encoding="utf-8") as f:
                # 读取所有行并去除空白字符
                words = [line.strip() for line in f.readlines() if line.strip()]

            # 验证词汇表完整性
            if len(words) != 2048:
                raise ValueError(
                    f"BIP-39英语词表应包含2048个单词，实际包含{len(words)}个"
                )

            # 验证第一个和最后一个单词
            if words[0] != "abandon" or words[2047] != "zoo":
                raise ValueError("BIP-39英语词表格式不正确")

            return words

        except FileNotFoundError:
            raise FileNotFoundError(f"未找到BIP-39英语词表文件: {wordlist_path}")
        except Exception as e:
            raise RuntimeError(f"加载BIP-39英语词表时出错: {str(e)}")

    def get_wordlist(self, language: str = "english") -> List[str]:
        """
        获取指定语言的词汇表

        Args:
            language (str): 语言代码，目前只支持'english'

        Returns:
            List[str]: 词汇表列表

        Raises:
            ValueError: 不支持的语言
        """
        if language != "english":
            raise ValueError(f"不支持的语言: {language}，目前只支持'english'")

        return self._english_wordlist.copy()

    def get_supported_languages(self) -> List[str]:
        """
        获取支持的语言列表

        Returns:
            List[str]: 支持的语言代码列表
        """
        return ["english"]

    def validate_word(self, word: str, language: str = "english") -> bool:
        """
        验证单词是否在指定语言的词汇表中

        Args:
            word (str): 要验证的单词
            language (str): 语言代码

        Returns:
            bool: 是否为有效单词
        """
        if language != "english":
            return False

        return word.lower() in self._english_wordlist

    def get_word_index(self, word: str, language: str = "english") -> Optional[int]:
        """
        获取单词在词汇表中的索引

        Args:
            word (str): 单词
            language (str): 语言代码

        Returns:
            Optional[int]: 单词索引，如果不存在则返回None
        """
        if language != "english":
            return None

        try:
            return self._english_wordlist.index(word.lower())
        except ValueError:
            return None

    def get_word_by_index(self, index: int, language: str = "english") -> Optional[str]:
        """
        根据索引获取单词

        Args:
            index (int): 词汇索引
            language (str): 语言代码

        Returns:
            Optional[str]: 对应的单词，如果索引无效则返回None
        """
        if language != "english":
            return None

        if 0 <= index < len(self._english_wordlist):
            return self._english_wordlist[index]
        return None

    def get_wordlist_info(self, language: str = "english") -> Dict:
        """
        获取词汇表信息

        Args:
            language (str): 语言代码

        Returns:
            Dict: 词汇表信息字典
        """
        if language != "english":
            return {}

        return {
            "language": "english",
            "total_words": len(self._english_wordlist),
            "first_word": self._english_wordlist[0],
            "last_word": self._english_wordlist[-1],
            "standard": "BIP-39",
            "source": "https://github.com/bitcoin/bips/tree/master/bip-0039",
        }

    def search_words(
        self, prefix: str, language: str = "english", limit: int = 10
    ) -> List[str]:
        """
        搜索以指定前缀开头的单词

        Args:
            prefix (str): 搜索前缀
            language (str): 语言代码
            limit (int): 返回结果限制

        Returns:
            List[str]: 匹配的单词列表
        """
        if language != "english":
            return []

        prefix = prefix.lower()
        matches = [word for word in self._english_wordlist if word.startswith(prefix)]
        return matches[:limit]


# 全局实例
_wordlist_manager = WordlistManager()


def get_wordlist(language: str = "english") -> List[str]:
    """
    获取指定语言的词汇表（快捷函数）

    Args:
        language (str): 语言代码

    Returns:
        List[str]: 词汇表列表
    """
    return _wordlist_manager.get_wordlist(language)


def validate_word(word: str, language: str = "english") -> bool:
    """
    验证单词是否有效（快捷函数）

    Args:
        word (str): 要验证的单词
        language (str): 语言代码

    Returns:
        bool: 是否为有效单词
    """
    return _wordlist_manager.validate_word(word, language)


def get_supported_languages() -> List[str]:
    """
    获取支持的语言列表（快捷函数）

    Returns:
        List[str]: 支持的语言代码列表
    """
    return _wordlist_manager.get_supported_languages()
