"""
输出格式化模块 - 精简版
负责将钱包信息格式化为Markdown格式
"""

import datetime
import os
from dataclasses import dataclass
from typing import Dict, List, Optional

from core.card_split import CardSplit
from core.derivation import DerivedAddress
from core.shamir import ShamirShare


class OutputFormatter:
    """输出格式化器 - 精简版"""

    def format_wallet_info(
        self,
        mnemonic: str,
        seed_hex: str,
        master_key_info: Dict,
        addresses: Dict[str, List[DerivedAddress]],
        generation_params: Dict,
        split_info: Optional[Dict] = None,
        verification_code: Optional[str] = None,
        verification_info: Optional[Dict] = None,
    ) -> str:
        """格式化完整的钱包信息"""
        content = []

        # 标题和警告
        content.extend(self._generate_header())
        content.append("")

        # 安全警告
        content.extend(self._generate_security_warning())
        content.append("")

        # 生成信息
        content.extend(self._format_generation_info(generation_params))
        content.append("")

        # 助记词部分
        content.extend(self._format_mnemonic_section(mnemonic))
        content.append("")

        # 验证码部分（如果有）
        if verification_code:
            content.extend(self._format_verification_section(verification_code, verification_info))
            content.append("")

        # 种子信息
        content.extend(self._format_seed_section(seed_hex))
        content.append("")

        # 主密钥信息
        content.extend(self._format_master_key_section(master_key_info))
        content.append("")

        # 派生地址
        content.extend(self._format_addresses_section(addresses))
        content.append("")

        # 分割信息（如果有）
        if split_info:
            content.extend(self._format_split_section(split_info))
            content.append("")

        # 安全建议和使用说明
        content.extend(self._generate_security_recommendations())
        content.append("")
        content.extend(self._generate_usage_instructions())

        return "\n".join(content)

    def save_wallet_info(self, wallet_info: Dict, output_file: str) -> str:
        """保存钱包信息到文件"""
        content = self.format_wallet_info(**wallet_info)
        
        # 确保目录存在
        os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else ".", exist_ok=True)
        
        # 保存文件
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(content)
        
        return output_file

    def _generate_header(self) -> List[str]:
        """生成文档头部"""
        return [
            "# 🔐 WalletX 钱包生成报告",
            "",
            "**⚠️ 机密文档 - 请妥善保管**",
            "",
            f"**生成时间**: {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC",
            "**文档版本**: WalletX v1.0.0 (安全增强版)"
        ]

    def _generate_security_warning(self) -> List[str]:
        """生成安全警告"""
        return [
            "## ⚠️ 关键安全警告",
            "",
            "**🔒 绝对保密性要求：**",
            "",
            "1. **此文档包含私钥信息** - 任何获得此文档的人都能完全控制您的加密资产",
            "2. **立即离线存储** - 请将此文档保存到离线存储设备，删除所有数字副本",
            "3. **物理安全** - 建议打印后存放在保险箱或银行保险柜中",
            "4. **多重备份** - 制作2-3份独立备份，分别存放在不同的安全位置",
            "5. **定期验证** - 定期检查备份的完整性和可读性",
            "",
            "**🚨 如果怀疑此文档已被泄露，请立即转移所有资产到新钱包！**"
        ]

    def _generate_security_recommendations(self) -> List[str]:
        """生成安全建议"""
        return [
            "## 🛡️ 高级安全建议",
            "",
            "### 助记词管理",
            "- 建议将助记词刻在金属板上，防火防水防腐蚀",
            "- 使用专业的助记词存储产品（如Cryptosteel）",
            "- 避免将助记词存储在任何电子设备上",
            "",
            "### 定期检查",
            "- 每6个月检查一次备份的物理状态",
            "- 每年验证一次助记词的有效性（在安全环境中）",
            "- 保持对技术标准更新的关注"
        ]

    def _format_generation_info(self, params: Dict) -> List[str]:
        """格式化生成参数信息"""
        content = ["## 生成参数", ""]
        content.append(f"- **助记词长度**: {params.get('word_count', 'N/A')} 个单词")
        content.append(f"- **熵长度**: {params.get('entropy_bits', 'N/A')} 位")
        content.append(f"- **语言**: {params.get('language', 'english')}")
        content.append(f"- **密码短语**: {'是' if params.get('passphrase') else '否'}")
        content.append(f"- **派生地址数量**: {params.get('address_count', 5)}")
        return content

    def _format_mnemonic_section(self, mnemonic: str) -> List[str]:
        """格式化助记词部分"""
        words = mnemonic.split()
        content = ["## 助记词 (Mnemonic Phrase)", "", "### 完整助记词", "```", mnemonic, "```", "", "### 按序号排列"]
        
        # 创建表格
        rows = []
        for i in range(0, len(words), 4):
            row_words = words[i:i+4]
            row = " | ".join([f"{i+j+1:2d}. {word}" for j, word in enumerate(row_words)])
            rows.append(f"| {row} |")
        
        content.extend(rows)
        return content

    def _format_verification_section(self, verification_code: str, verification_info: Optional[Dict] = None) -> List[str]:
        """格式化验证码部分"""
        content = [
            "## 🔑 助记词验证码 (EMVC)",
            "",
            "### 验证码",
            "```",
            verification_code,
            "```",
            "",
            "### 验证码说明",
            "",
        ]
        
        if verification_info and verification_info.get('valid_format'):
            content.extend([
                f"- **格式**: {verification_info.get('format', 'XXXX-YYYY')}",
                f"- **数字部分**: {verification_info.get('digits_part', 'N/A')}",
                f"- **字母部分**: {verification_info.get('letters_part', 'N/A')}",
                f"- **安全熵**: {verification_info.get('entropy_bits', 64)} 位",
                f"- **说明**: {verification_info.get('description', '助记词唯一验证码')}",
                "",
                "### 用途说明",
                "",
                "**🔍 验证码用途**：",
                "- 在恢复助记词时验证输入的正确性",
                "- 确认助记词的完整性和一致性",
                "- 防止助记词输入错误或被篡改",
                "",
                "**📝 使用方法**：",
                "1. 记录此验证码并与助记词分开保存",
                "2. 恢复钱包时，输入助记词后验证码应一致",
                "3. 如验证码不匹配，说明助记词有误",
                "",
                "**⚠️ 安全提醒**：",
                "- 验证码本身不含助记词信息，相对安全",
                "- 但仍建议与助记词一样妥善保管",
                "- 验证码可用于验证备份的完整性"
            ])
        else:
            content.extend([
                "- 验证码格式验证失败",
                "- 请检查验证码生成过程"
            ])
        
        return content

    def _format_seed_section(self, seed_hex: str) -> List[str]:
        """格式化种子部分"""
        return [
            "## 种子 (Seed)",
            "",
            f"**长度**: {len(seed_hex)//2} 字节 ({len(seed_hex)*4} 位)",
            "",
            "```",
            seed_hex,
            "```"
        ]

    def _format_master_key_section(self, master_key_info: Dict) -> List[str]:
        """格式化主密钥部分"""
        return [
            "## 主密钥 (Master Key)",
            "",
            f"**主私钥**: `{master_key_info.get('private_key', 'N/A')}`",
            "",
            f"**链码**: `{master_key_info.get('chain_code', 'N/A')}`",
            "",
            f"**深度**: {master_key_info.get('depth', 0)}",
            "",
            f"**指纹**: `{master_key_info.get('fingerprint', '00000000')}`"
        ]

    def _format_addresses_section(self, addresses: Dict[str, List[DerivedAddress]]) -> List[str]:
        """格式化派生地址部分 - 在表格中直接展示完整的公钥和私钥信息"""
        content = ["## 派生地址 (Derived Addresses)", ""]
        
        # 处理空地址字典的情况
        if not addresses:
            content.extend([
                "⚠️ **地址生成失败**",
                "",
                "没有成功生成任何网络的地址。可能的原因：",
                "- 网络配置错误",
                "- 密钥派生过程出现异常",
                "- 系统依赖问题",
                "",
                "建议：",
                "1. 检查网络名称是否正确",
                "2. 确保所有必要的依赖已安装",
                "3. 重新尝试生成钱包",
                ""
            ])
            return content
        
        for network, addr_list in addresses.items():
            content.append(f"### {network.upper()} 网络")
            content.append("")
            
            # 处理特定网络地址为空的情况
            if not addr_list:
                content.extend([
                    f"⚠️ {network.upper()} 网络地址生成失败",
                    ""
                ])
                continue
            
            # 根据网络类型选择不同的表格格式
            if network.lower() == "bitcoin":
                # 比特币网络：显示HEX和WIF两种私钥格式
                content.extend([
                    "| 索引 | 地址 | 完整私钥 (HEX) | 完整私钥 (WIF) | 完整公钥 | 派生路径 |",
                    "|------|------|----------------|----------------|----------|----------|"
                ])
                
                for addr in addr_list:
                    content.append(f"| {addr.index} | `{addr.address}` | `{addr.private_key}` | `{addr.private_key_wif}` | `{addr.public_key}` | `{addr.path}` |")
            else:
                # 其他网络：标准格式
                content.extend([
                    "| 索引 | 地址 | 完整私钥 | 完整公钥 | 派生路径 |",
                    "|------|------|----------|----------|----------|"
                ])
                
                for addr in addr_list:
                    content.append(f"| {addr.index} | `{addr.address}` | `{addr.private_key}` | `{addr.public_key}` | `{addr.path}` |")
            
            content.append("")
        
        return content

    def _format_split_section(self, split_info: Dict) -> List[str]:
        """格式化分割信息部分"""
        if split_info.get("mode") == "card":
            return self._format_card_split_info(split_info)
        elif split_info.get("mode") == "shamir":
            return self._format_shamir_split_info(split_info)
        return []

    def _format_card_split_info(self, split_info: Dict) -> List[str]:
        """格式化卡片分割信息"""
        return [
            "## 🃏 卡片分割信息",
            "",
            f"- **分割模式**: 卡片分割",
            f"- **卡片数量**: {split_info.get('card_count', 'N/A')}",
            f"- **重叠比例**: {split_info.get('overlap_ratio', 'N/A')}",
            "",
            "**注意**: 卡片分割文件已单独保存"
        ]

    def _format_shamir_split_info(self, split_info: Dict) -> List[str]:
        """格式化Shamir分割信息"""
        return [
            "## 🔐 Shamir分割信息",
            "",
            f"- **分割模式**: Shamir秘密分享",
            f"- **恢复阈值**: {split_info.get('threshold', 'N/A')}",
            f"- **总分片数**: {split_info.get('total_shares', 'N/A')}",
            "",
            "**注意**: Shamir分片文件已单独保存"
        ]

    def _generate_usage_instructions(self) -> List[str]:
        """生成使用说明"""
        return [
            "## 使用说明",
            "",
            "### 导入钱包",
            "1. 打开支持BIP-39的钱包应用",
            "2. 选择'导入钱包'或'恢复钱包'选项",
            "3. 按顺序输入上述助记词",
            "4. 如果设置了密码短语，请同时输入",
            "5. 确认导入，钱包将自动派生对应地址",
            "",
            "### 验证地址",
            "- 导入后请验证生成的地址是否与上述列表一致",
            "- 如果地址不匹配，请检查助记词输入是否正确",
            "",
            "### 安全建议",
            "- 首次使用前，建议先用小额资金测试",
            "- 确认能够正常接收和发送交易后再转入大额资金",
            "- 定期备份钱包文件，但助记词是最终的恢复手段",
            "",
            "---",
            "",
            "*本文件由 Web3钱包助记词生成器 生成*",
            "",
            f"*生成时间: {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}*"
        ]

    def format_card_split_output(self, cards: List[CardSplit], instructions: str) -> str:
        """格式化卡片分割输出 - 按PRD格式显示"""
        content = [
            "# 助记词卡片分割输出（错位分散算法）",
            f"**生成时间**: {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**算法**: 错位分散（Staggered Dispersion）- 符合PRD规范",
            "",
            "## ⚠️ 重要安全提示",
            "",
            "- 每张卡片都包含部分助记词信息，使用错位分散算法",
            "- 需要**所有卡片**才能完整恢复助记词",
            "- XXXX占位符错位分散，避免连续出现",
            "- 基于模运算 `i % total_cards == (card_id - 1)` 分配掩码位置",
            "- 请将卡片分别存储在不同的安全位置",
            "- 丢失任何一张卡片都可能导致无法恢复钱包",
            ""
        ]
        
        # 按PRD格式显示卡片
        for card in cards:
            content.extend([
                f"## 卡片 {card.card_id}/{card.total_cards}",
                "",
                "**卡片内容**（按PRD格式）:",
                "```",
                f"{card.display_card()}",
                "```",
                "",
                f"**验证码**: {card.verification_code[:8]}",
                f"**掩码位置**: {sorted(card.masked_positions)}",
                f"**算法**: {card.metadata.get('algorithm', 'staggered_dispersion')}",
                f"**安全级别**: {card.metadata.get('security_level', '中')}",
                "",
                "**存储建议**: 请将此卡片存储在安全的离线位置",
                ""
            ])
        
        content.extend([
            "## 恢复说明",
            "",
            instructions,
            "",
            "## PRD规范说明",
            "",
            "本分割方案严格按照PRD（产品需求文档）规范实现：",
            "- ✅ 使用错位分散算法",
            "- ✅ 基于模运算 `i % total_cards == (card_id - 1)` 分配",
            "- ✅ XXXX占位符错位分散，避免连续出现",
            "- ✅ 不同卡片的隐藏位置完全不重叠",
            "- ✅ 提高安全性和美观度",
            "",
            f"**示例验证**: Card 1 隐藏位置 {[i for i in range(len(cards[0].words)) if i % cards[0].total_cards == 0][:5]}..."
        ])
        
        return "\n".join(content)

    def format_shamir_output(self, shares: List[ShamirShare], recovery_info: Dict, original_mnemonic: str = None) -> str:
        """格式化Shamir输出 - 按PRD规范实现"""
        content = [
            "# Shamir秘密分享输出（PRD规范实现）",
            f"**生成时间**: {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**算法**: Shamir秘密分享 - 符合PRD规范",
            "",
            "## ⚠️ 重要说明",
            "",
            "**本文件包含Shamir分片信息，请妥善保管！**",
            "",
            "- 分片是从原始助记词生成的，可以用于恢复原始助记词",
            "- 出于安全考虑，原始助记词不在此文件中显示",
            "- 请将此文件存储在安全的离线环境中",
            "- 不要在网络环境中传输或存储此文件",
            "",
        ]
        
        # 不再显示原始助记词以提高安全性
        if original_mnemonic:
            content.extend([
                "## 📝 原始助记词信息",
                "",
                f"**助记词长度**: {len(original_mnemonic.split())} 个单词",
                f"**分片用途**: 此助记词已使用Shamir算法分割成 {len(shares)} 个分片",
                "",
                "**安全提醒**: 出于安全考虑，原始助记词不在分片文件中显示",
                "**备份提醒**: 请确保您已在其他安全位置备份了原始助记词",
                ""
            ])
        
        content.extend([
            "## 分片信息概览",
            "",
            f"- **总分片数**: {len(shares)}",
            f"- **恢复阈值**: {recovery_info.get('threshold', 'N/A')}",
            f"- **当前分片数**: {len(shares)}",
            f"- **可恢复**: {'是' if len(shares) >= recovery_info.get('threshold', 0) else '否'}",
            f"- **原始助记词长度**: {recovery_info.get('original_word_count', '未知')} 个单词",
            f"- **需要密码短语**: {'是' if recovery_info.get('passphrase_used', False) else '否'}",
            f"- **安全级别**: {recovery_info.get('security_level', '中')}",
        ])

        # 添加原始验证码信息
        original_verification_code = recovery_info.get('original_verification_code')
        if original_verification_code:
            content.extend([
                f"- **原始验证码**: {original_verification_code}",
                "",
                "**验证码说明**:",
                "- 此验证码用于验证恢复后助记词的正确性",
                "- 恢复时系统会自动生成验证码并与此进行比对",
                "- 验证码匹配表示助记词恢复成功且完整"
            ])

        content.extend([
            "",
            "## 分片详情（助记词格式）",
            ""
        ])
        
        for share in shares:
            content.extend([
                f"### 分片 {share.share_id}",
                "",
                "**分片助记词**（按PRD要求生成的BIP-39格式）:",
                "```",
                share.share_mnemonic,
                "```",
                "",
                "**分片参数**:",
                f"- 分片ID: {share.share_id}",
                f"- 阈值: {share.threshold}",
                f"- 总数: {share.total_shares}",
                f"- 算法: {share.metadata.get('algorithm', 'shamir_secret_sharing')}",
                f"- 编码: {share.metadata.get('encoding', 'bip39_mnemonic')}",
                "",
                "**重要提醒**: 此助记词是分片表示，不能直接用作钱包助记词",
                ""
            ])
        
        content.extend([
            "## PRD规范实现说明",
            "",
            "本Shamir分割严格按照PRD规范实现：",
            "- ✅ 将原始助记词转换为种子",
            "- ✅ 使用Shamir算法分割种子", 
            "- ✅ 为每个分片生成助记词表示",
            "- ✅ 支持N-of-M分片恢复机制",
            "- ✅ 完整的分片验证和重构功能",
            "",
            "## 恢复说明",
            "",
            f"1. **收集分片**: 需要至少 {recovery_info.get('threshold', 'N/A')} 个分片",
            "2. **使用WalletX**: 本工具支持Shamir分片恢复功能",
            "3. **输入分片助记词**: 按分片ID顺序输入助记词",
            "4. **提供密码短语**: 如果原始助记词使用了密码短语",
            "5. **验证恢复**: 确认恢复的原始助记词正确性",
            "",
            "### 恢复命令示例",
            "```bash",
            f"# 使用 {recovery_info.get('threshold', 'N/A')} 个分片恢复原始助记词",
            "python src/main.py --recover-shamir --threshold {threshold} --shares 'share1,share2,share3'".format(
                threshold=recovery_info.get('threshold', 3)
            ),
            "```",
            "",
            "**安全提醒**:",
            "- 分片分别存储在不同的安全位置",
            "- 定期验证分片的完整性和可读性",
            "- 恢复操作建议在离线环境中进行",
        ])
        
        return "\n".join(content)

    def format_single_shamir_share(self, share: ShamirShare, recovery_info: Dict, original_mnemonic: str = None) -> str:
        """格式化单个Shamir分片输出 - 用于生成单独的分片文件"""
        content = [
            f"# Shamir分片 {share.share_id}/{share.total_shares}（PRD规范实现）",
            f"**生成时间**: {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**算法**: Shamir秘密分享 - 符合PRD规范",
            "",
            "## ⚠️ 重要安全提示",
            "",
            "**本文件包含单个Shamir分片信息，请妥善保管！**",
            "",
            "- 这是一个Shamir分片，需要与其他分片组合使用才能恢复原始助记词",
            f"- 需要至少 {recovery_info.get('threshold', 'N/A')} 个分片才能恢复",
            f"- 当前是第 {share.share_id} 个分片，共 {share.total_shares} 个",
            "- 出于安全考虑，原始助记词不在此文件中显示",
            "- 请将此分片存储在安全的离线环境中",
            "- 不要在网络环境中传输或存储此文件",
            "",
        ]
        
        # 添加原始助记词信息（不显示具体内容）
        if original_mnemonic:
            content.extend([
                "## 📝 原始助记词信息",
                "",
                f"**助记词长度**: {len(original_mnemonic.split())} 个单词",
                f"**总分片数**: {share.total_shares}",
                f"**恢复阈值**: {recovery_info.get('threshold', 'N/A')}",
                "",
                "**安全提醒**: 出于安全考虑，原始助记词不在分片文件中显示",
                "**备份提醒**: 请确保您已在其他安全位置备份了原始助记词",
                ""
            ])
        
        content.extend([
            "## 分片信息",
            "",
            f"- **分片ID**: {share.share_id}",
            f"- **总分片数**: {share.total_shares}",
            f"- **恢复阈值**: {share.threshold}",
            f"- **原始助记词长度**: {recovery_info.get('original_word_count', '未知')} 个单词",
            f"- **需要密码短语**: {'是' if recovery_info.get('passphrase_used', False) else '否'}",
            f"- **安全级别**: {recovery_info.get('security_level', '中')}",
        ])

        # 添加原始验证码信息
        original_verification_code = recovery_info.get('original_verification_code')
        if original_verification_code:
            content.extend([
                f"- **原始验证码**: {original_verification_code}",
                "",
                "**验证码说明**:",
                "- 此验证码用于验证恢复后助记词的正确性",
                "- 恢复时系统会自动生成验证码并与此进行比对",
                "- 验证码匹配表示助记词恢复成功且完整"
            ])
        
        content.extend([
            "",
            "## 分片助记词",
            "",
            "**分片助记词**（按PRD要求生成的BIP-39格式）:",
            "```",
            share.share_mnemonic,
            "```",
            "",
            "**分片参数**:",
            f"- 分片ID: {share.share_id}",
            f"- 阈值: {share.threshold}",
            f"- 总数: {share.total_shares}",
            f"- 算法: {share.metadata.get('algorithm', 'shamir_secret_sharing')}",
            f"- 编码: {share.metadata.get('encoding', 'bip39_mnemonic')}",
            "",
            "**重要提醒**: 此助记词是分片表示，不能直接用作钱包助记词",
            "",
            "## PRD规范实现说明",
            "",
            "本Shamir分片严格按照PRD规范实现：",
            "- ✅ 从原始助记词转换为种子",
            "- ✅ 使用Shamir算法分割种子", 
            "- ✅ 为分片生成助记词表示",
            "- ✅ 支持N-of-M分片恢复机制",
            "- ✅ 完整的分片验证和重构功能",
            "",
            "## 恢复说明",
            "",
            f"1. **收集分片**: 需要至少 {recovery_info.get('threshold', 'N/A')} 个分片",
            "2. **使用WalletX**: 本工具支持Shamir分片恢复功能",
            "3. **输入分片助记词**: 按分片ID顺序输入助记词",
            "4. **提供密码短语**: 如果原始助记词使用了密码短语",
            "5. **验证恢复**: 确认恢复的原始助记词正确性",
            "",
            "### 恢复命令示例",
            "```bash",
            f"# 使用 {recovery_info.get('threshold', 'N/A')} 个分片恢复原始助记词",
            "python src/main.py --recover-shamir --threshold {threshold} --shares 'share1,share2,share3'".format(
                threshold=recovery_info.get('threshold', 3)
            ),
            "```",
            "",
            "**安全提醒**:",
            "- 将此分片与其他分片分别存储在不同的安全位置",
            "- 定期验证分片的完整性和可读性",
            "- 恢复操作建议在离线环境中进行",
            "",
            "---",
            "",
            f"*本分片文件由 Web3钱包助记词生成器 生成*",
            f"*分片 {share.share_id}/{share.total_shares} - 生成时间: {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}*"
        ])
        
        return "\n".join(content)
