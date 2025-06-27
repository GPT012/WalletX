"""
卡片分割模块
实现助记词的卡片分割和恢复功能 - 按PRD规范实现错位分散算法
"""

import hashlib
import secrets
from dataclasses import dataclass
from typing import Dict, List


@dataclass
class CardSplitResult:
    """卡片分割结果类"""
    cards: List['CardSplit']
    original_mnemonic: str
    algorithm: str
    instructions: str


@dataclass
class CardSplit:
    """卡片分割数据类"""

    card_id: int
    words: List[str]
    masked_positions: List[int]
    total_cards: int
    verification_code: str
    metadata: Dict[str, str]

    @property
    def card_content(self) -> str:
        """卡片显示内容（符合PRD格式）"""
        display_words = []
        for i, word in enumerate(self.words):
            if i in self.masked_positions:
                display_words.append("XXXX")
            else:
                display_words.append(word)
        return " ".join(display_words)

    def display_card(self) -> str:
        """显示卡片内容"""
        return f"Card {self.card_id}: {self.card_content}"

    def display_format(self) -> str:
        """PRD格式的卡片显示方法"""
        return self.card_content


class CardSplitter:
    """
    卡片分割器类 - 按PRD规范实现错位分散算法
    实现助记词的卡片分割功能
    """

    def __init__(self):
        """初始化卡片分割器"""
        pass

    def split_to_cards(self, mnemonic: str, num_cards: int = 3):
        """
        主接口：将助记词分割为卡片
        返回卡片分割结果对象
        """
        cards = self.split_mnemonic(mnemonic, num_cards)
        
        return CardSplitResult(
            cards=cards,
            original_mnemonic=mnemonic,
            algorithm="staggered_dispersion",
            instructions=self.create_recovery_instructions(cards)
        )

    def split_mnemonic(
        self, mnemonic: str, num_cards: int = 3
    ) -> List[CardSplit]:
        """
        将助记词分割为多张卡片 - 按PRD错位分散算法

        Args:
            mnemonic (str): 原始助记词
            num_cards (int): 卡片数量

        Returns:
            List[CardSplit]: 卡片列表
        """
        words = mnemonic.strip().split()
        word_count = len(words)

        if num_cards < 2:
            raise ValueError("卡片数量必须至少为2")
        if num_cards > word_count:
            raise ValueError(f"卡片数量不能超过助记词数量({word_count})")

        cards = []

        # 生成验证码（基于助记词哈希）
        verification_base = hashlib.sha256(mnemonic.encode()).hexdigest()

        for card_id in range(1, num_cards + 1):
            # 使用PRD规定的错位分散算法
            # 基于模运算: i % total_cards == (card_id - 1)
            masked_positions = self._generate_staggered_mask_pattern(
                word_count, card_id, num_cards
            )

            # 为每张卡片生成唯一验证码
            card_verification = hashlib.sha256(
                f"{verification_base}-card-{card_id}".encode()
            ).hexdigest()

            card = CardSplit(
                card_id=card_id,
                words=words.copy(),
                masked_positions=masked_positions,
                total_cards=num_cards,
                verification_code=card_verification,
                metadata={
                    "word_count": str(word_count),
                    "algorithm": "staggered_dispersion",
                    "creation_time": verification_base[:16],
                    "security_level": self._calculate_security_level(word_count, num_cards),
                },
            )
            cards.append(card)

        return cards

    def _generate_staggered_mask_pattern(
        self, word_count: int, card_id: int, total_cards: int
    ) -> List[int]:
        """
        生成错位分散掩码模式 - 严格按PRD规范
        使用轮转算法确保XXXX占位符错位分散，避免连续出现
        基于模运算 i % total_cards == (card_id - 1) 分配掩码位置

        Args:
            word_count (int): 总单词数
            card_id (int): 卡片ID (1-based)
            total_cards (int): 总卡片数

        Returns:
            List[int]: 被掩码的位置列表
        """
        masked_positions = []
        
        # 按PRD规范：基于模运算分配掩码位置
        # 卡片1掩码: i % total_cards == 0 的位置
        # 卡片2掩码: i % total_cards == 1 的位置
        # 以此类推...
        
        for i in range(word_count):
            if i % total_cards == (card_id - 1):
                masked_positions.append(i)

        return masked_positions

    def _calculate_security_level(self, word_count: int, num_cards: int) -> str:
        """计算安全级别"""
        # 计算每张卡片平均隐藏的单词数
        hidden_per_card = word_count // num_cards
        
        # 计算暴力破解复杂度: 2^(隐藏词数 × log2(2048))位
        security_bits = hidden_per_card * 11  # log2(2048) ≈ 11
        
        if security_bits >= 128:
            return "高"
        elif security_bits >= 64:
            return "中"
        else:
            return "低"

    def reconstruct_mnemonic(self, cards: List[CardSplit]) -> str:
        """
        从卡片重构原始助记词

        Args:
            cards (List[CardSplit]): 卡片列表

        Returns:
            str: 重构的助记词

        Raises:
            ValueError: 如果卡片数据不完整或不一致
        """
        if not cards:
            raise ValueError("需要至少一张卡片")

        # 验证卡片一致性
        word_count = len(cards[0].words)
        total_cards = cards[0].total_cards

        for card in cards[1:]:
            if len(card.words) != word_count or card.total_cards != total_cards:
                raise ValueError("卡片数据不一致")

        if len(cards) != total_cards:
            raise ValueError(f"需要所有{total_cards}张卡片才能恢复助记词")

        # 重构助记词
        reconstructed_words = [""] * word_count
        coverage = [False] * word_count

        # 从每张卡片收集未掩码的单词
        for card in cards:
            for i, word in enumerate(card.words):
                if i not in card.masked_positions:
                    if reconstructed_words[i] == "":
                        reconstructed_words[i] = word
                        coverage[i] = True
                    elif reconstructed_words[i] != word:
                        raise ValueError(f"位置{i}的单词在不同卡片中不一致")

        # 检查是否所有位置都有单词
        missing_positions = [i for i, covered in enumerate(coverage) if not covered]
        if missing_positions:
            raise ValueError(f"无法恢复位置{missing_positions}的单词，可能缺少卡片")

        return " ".join(reconstructed_words)

    def validate_cards(self, cards: List[CardSplit]) -> bool:
        """
        验证卡片组合的有效性

        Args:
            cards (List[CardSplit]): 卡片列表

        Returns:
            bool: 是否有效
        """
        if not cards:
            return False

        try:
            # 尝试重构助记词
            self.reconstruct_mnemonic(cards)
            return True
        except ValueError:
            return False

    def estimate_security(self, cards: List[CardSplit]) -> Dict:
        """
        评估分割方案的安全性

        Args:
            cards (List[CardSplit]): 卡片列表

        Returns:
            Dict: 安全性评估结果
        """
        if not cards:
            return {"error": "无卡片数据"}

        card = cards[0]
        word_count = len(card.words)
        total_cards = card.total_cards
        hidden_per_card = len(card.masked_positions)

        # 计算安全参数
        total_hidden_words = hidden_per_card * total_cards
        security_bits = hidden_per_card * 11  # log2(2048) ≈ 11
        
        # 计算破解时间（假设每秒尝试10^9次）
        attempts_per_second = 10**9
        total_combinations = 2048 ** hidden_per_card
        crack_time_seconds = total_combinations / (2 * attempts_per_second)  # 平均时间

        return {
            "word_count": word_count,
            "total_cards": total_cards,
            "hidden_per_card": hidden_per_card,
            "total_hidden_words": total_hidden_words,
            "security_bits": security_bits,
            "security_level": card.metadata.get("security_level", "未知"),
            "estimated_crack_time_years": crack_time_seconds / (365.25 * 24 * 3600),
            "algorithm": "staggered_dispersion_prd_compliant",
        }

    def _calculate_security_bits(self, combinations: int) -> int:
        """计算安全位数"""
        import math
        return int(math.log2(combinations))

    def generate_card_images(self, cards: List[CardSplit]) -> List[str]:
        """
        生成卡片的可视化表示

        Args:
            cards (List[CardSplit]): 卡片列表

        Returns:
            List[str]: 卡片图像字符串列表
        """
        images = []

        for card in cards:
            lines = [
                "╭─────────────────────────────────────────────╮",
                f"│  卡片 {card.card_id}/{card.total_cards}                                    │",
                "├─────────────────────────────────────────────┤",
                "│                                             │",
            ]

            # 分行显示助记词
            words = card.card_content.split()
            for i in range(0, len(words), 4):
                word_line = " ".join(words[i:i+4])
                lines.append(f"│  {word_line:<41} │")

            lines.extend([
                "│                                             │",
                f"│  验证码: {card.verification_code[:8]:<32} │",
                "│                                             │",
                "╰─────────────────────────────────────────────╯",
                "",
            ])

            images.append("\n".join(lines))

        return images

    def create_recovery_instructions(self, cards: List[CardSplit]) -> str:
        """
        创建恢复说明

        Args:
            cards (List[CardSplit]): 卡片列表

        Returns:
            str: 恢复说明文档
        """
        if not cards:
            return "无卡片数据"

        card_sample = cards[0]
        security_info = self.estimate_security(cards)

        instructions = f"""
## 助记词恢复说明

### 基本信息
- **分割算法**: 错位分散（Staggered Dispersion）
- **卡片总数**: {card_sample.total_cards} 张
- **助记词长度**: {len(card_sample.words)} 个单词
- **安全级别**: {security_info.get('security_level', '未知')}

### 恢复步骤
1. **收集所有卡片**: 必须拥有全部 {card_sample.total_cards} 张卡片
2. **验证卡片**: 检查每张卡片的验证码前8位
3. **按序排列**: 按卡片编号1到{card_sample.total_cards}排列
4. **重构助记词**: 将每张卡片的可见单词合并，忽略XXXX

### 重构原理
- 每张卡片隐藏不同位置的单词（错位分散）
- 卡片{1}隐藏位置: {', '.join(map(str, [i for i in range(len(card_sample.words)) if i % card_sample.total_cards == 0]))}
- 所有卡片组合可完整恢复原始助记词

### 安全提醒
- **单张卡片**: 不足以恢复完整助记词
- **破解难度**: 约 {security_info.get('security_bits', 0)} 位安全强度
- **存储建议**: 将卡片分别存储在不同的安全位置
- **定期检查**: 验证卡片完整性和可读性

### 验证码
{chr(10).join([f"- 卡片{card.card_id}: {card.verification_code[:8]}" for card in cards])}
        """

        return instructions.strip()
