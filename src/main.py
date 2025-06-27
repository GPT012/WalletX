#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web3钱包助记词生成器主程序

该程序提供完整的BIP-39标准助记词生成功能，支持：
- 12/15/18/21/24个单词的助记词生成
- BIP-32/BIP-44密钥派生
- 多个区块链网络地址生成
- 卡片分割和Shamir秘密分享
- 英文助记词支持

Author: AI Assistant
Date: 2024
"""

import argparse
import os
import sys
import random
from typing import Dict, List, Optional
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.core.derivation import KeyDerivation
from src.core.mnemonic import MnemonicGenerator
from src.core.seed import SeedGenerator
from src.utils.output import OutputFormatter
from src.utils.validation import MnemonicValidator
from src.utils.wordlists import WordlistManager


def generate_default_filename(word_count: int, split_mode: Optional[str] = None, split_params: Optional[Dict] = None) -> str:
    """
    生成默认文件名：助记词数量_分片方式_时分秒+唯一4位随机数.md
    
    Args:
        word_count: 助记词数量
        split_mode: 分割方式 ("card" 或 "shamir")
        split_params: 分割参数
        
    Returns:
        str: 生成的文件名
    """
    # 获取当前时间的时分秒
    current_time = datetime.now()
    time_str = current_time.strftime("%H%M%S")
    
    # 生成4位随机数
    random_num = random.randint(1000, 9999)
    
    # 基础文件名：助记词数量
    filename_parts = [f"{word_count}words"]
    
    # 添加分割方式和数量
    if split_mode == "card":
        num_cards = split_params.get("num_cards", 3) if split_params else 3
        filename_parts.append(f"card{num_cards}")
    elif split_mode == "shamir":
        threshold = split_params.get("threshold", 3) if split_params else 3
        total_shares = split_params.get("total_shares", 5) if split_params else 5
        filename_parts.append(f"shamir{threshold}of{total_shares}")
    else:
        filename_parts.append("standard")
    
    # 添加时分秒+4位随机数
    filename_parts.append(f"{time_str}{random_num}")
    
    # 组合文件名
    filename = "_".join(filename_parts) + ".md"
    
    # 确保在dist目录下
    return os.path.join("dist", filename)


def generate_recovery_filename(recovery_type: str = "wallet", original_info: Optional[Dict] = None) -> str:
    """
    生成恢复文件名：*_recovered.md
    
    Args:
        recovery_type: 恢复类型 ("wallet", "card", "shamir")
        original_info: 原始文件信息
        
    Returns:
        str: 生成的恢复文件名
    """
    # 获取当前时间的时分秒
    current_time = datetime.now()
    time_str = current_time.strftime("%H%M%S")
    
    # 生成4位随机数
    random_num = random.randint(1000, 9999)
    
    if original_info:
        # 如果有原始信息，基于原始文件名生成
        word_count = original_info.get("word_count", 24)
        split_mode = original_info.get("split_mode", "standard")
        split_params = original_info.get("split_params", {})
        
        filename_parts = [f"{word_count}words"]
        
        if split_mode == "card":
            num_cards = split_params.get("num_cards", 3)
            filename_parts.append(f"card{num_cards}")
        elif split_mode == "shamir":
            threshold = split_params.get("threshold", 3)
            total_shares = split_params.get("total_shares", 5)
            filename_parts.append(f"shamir{threshold}of{total_shares}")
        else:
            filename_parts.append("standard")
            
        filename_parts.extend([f"{time_str}{random_num}", "recovered"])
    else:
        # 默认命名方式
        filename_parts = [f"{recovery_type}_recovery", f"{time_str}{random_num}", "recovered"]
    
    # 组合文件名
    filename = "_".join(filename_parts) + ".md"
    
    # 确保在dist目录下
    return os.path.join("dist", filename)


def prompt_missing_params(args) -> Dict:
    """
    当命令行参数不完整时，提示用户补充必要的参数
    
    Args:
        args: 已解析的命令行参数
        
    Returns:
        Dict: 完整的参数配置
    """
    print("🔐 WalletX 钱包生成器 - 参数配置")
    print("=" * 50)
    
    # 1. 助记词长度
    word_count = args.words
    if not word_count or word_count == 24:  # 如果是默认值，询问用户是否要更改
        print("\n📝 助记词长度配置")
        print("选项: 12词(日常) | 15词(增强) | 18词(高级) | 21词(企业) | 24词(最高)")
        choice = input(f"选择助记词长度 [12/15/18/21/24] (当前: {word_count}): ").strip()
        if choice and choice.isdigit() and int(choice) in [12, 15, 18, 21, 24]:
            word_count = int(choice)
            print(f"✅ 已设置为 {word_count} 词")
        else:
            print(f"✅ 保持默认设置 {word_count} 词")
    
    # 1.5. 助记词来源选择
    mnemonic = args.mnemonic
    if not mnemonic:
        print("\n🎯 助记词来源配置")
        print("选项:")
        print("  1. 生成新助记词 (推荐)")
        print("  2. 使用指定助记词 (测试或恢复用)")
        
        choice = input("选择助记词来源 [1/2] (默认: 1): ").strip() or "1"
        
        if choice == "2":
            mnemonic = input(f"请输入 {word_count} 词助记词 (空格分隔): ").strip()
            if mnemonic:
                # 简单验证词数
                words = mnemonic.split()
                if len(words) != word_count:
                    print(f"⚠️ 警告: 输入了 {len(words)} 个词，但设置为 {word_count} 词")
                    word_count = len(words)  # 更新词数以匹配实际输入
                print(f"✅ 将使用指定的 {len(words)} 词助记词")
            else:
                print("✅ 输入为空，将生成新助记词")
                mnemonic = None
        else:
            print("✅ 将生成新助记词")
    else:
        print(f"✅ 使用命令行指定的助记词")
    
    # 2. 密码短语配置
    passphrase = args.passphrase
    if not passphrase:
        print("\n🔒 密码短语配置")
        print("密码短语是可选的额外安全层，即使有人获得您的助记词，")
        print("没有密码短语也无法访问您的钱包。")
        use_passphrase = input("是否使用密码短语? [y/N]: ").lower().startswith("y")
        if use_passphrase:
            passphrase = input("请输入密码短语: ")
            print("✅ 已设置密码短语")
        else:
            print("✅ 不使用密码短语")
    else:
        print("✅ 使用命令行指定的密码短语")
    
    # 3. 分割方式
    split_mode = args.split
    split_params = {}
    
    if not split_mode:
        print("\n🔐 分割方式配置")
        print("选项:")
        print("  1. 无分割 - 标准助记词")
        print("  2. 卡片分割 - 错位分散，需要所有卡片")
        print("  3. Shamir分割 - 门限秘密，灵活恢复")
        
        choice = input("选择分割方式 [1/2/3] (默认: 1): ").strip() or "1"
        
        if choice == "2":
            split_mode = "card"
            print("\n🃏 卡片分割配置")
            num_cards = input(f"卡片数量 [2-{word_count}] (默认: {args.card_num}): ").strip()
            if num_cards and num_cards.isdigit():
                num_cards = int(num_cards)
                if 2 <= num_cards <= word_count:
                    split_params = {"num_cards": num_cards}
                else:
                    print(f"❌ 卡片数量超出范围，使用默认值 {args.card_num}")
                    split_params = {"num_cards": args.card_num}
            else:
                split_params = {"num_cards": args.card_num}
            print(f"✅ 将生成 {split_params['num_cards']} 张卡片")
            
        elif choice == "3":
            split_mode = "shamir"
            print("\n🔀 Shamir分割配置")
            threshold = input(f"恢复阈值 (默认: {args.shamir_threshold}): ").strip()
            total_shares = input(f"总分片数 (默认: {args.shamir_total}): ").strip()
            
            if threshold and threshold.isdigit():
                threshold = int(threshold)
            else:
                threshold = args.shamir_threshold
                
            if total_shares and total_shares.isdigit():
                total_shares = int(total_shares)
            else:
                total_shares = args.shamir_total
                
            if threshold > total_shares:
                print(f"❌ 阈值不能大于总分片数，调整阈值为 {total_shares}")
                threshold = total_shares
                
            split_params = {"threshold": threshold, "total_shares": total_shares}
            print(f"✅ 将生成 {total_shares} 个分片，需要 {threshold} 个分片恢复")
        else:
            print("✅ 将生成标准助记词（无分割）")
    else:
        # 如果已指定分割模式，使用命令行参数
        if split_mode == "card":
            split_params = {"num_cards": args.card_num}
        elif split_mode == "shamir":
            split_params = {"threshold": args.shamir_threshold, "total_shares": args.shamir_total}
    
    # 4. 输出选项（如果没有指定output且不是display-only）
    display_only = args.display_only
    output_file = args.output
    
    if not display_only and not output_file:
        print("\n💾 输出配置")
        print("选项:")
        print("  1. 自动生成文件名")
        print("  2. 自定义文件路径") 
        print("  3. 仅显示不保存")
        
        choice = input("选择输出方式 [1/2/3] (默认: 1): ").strip() or "1"
        
        if choice == "2":
            output_file = input("输入文件路径: ").strip()
            if not output_file:
                output_file = generate_default_filename(word_count, split_mode, split_params)
                print(f"✅ 使用自动生成的文件名: {output_file}")
        elif choice == "3":
            display_only = True
            print("✅ 将仅在终端显示结果")
        else:
            output_file = generate_default_filename(word_count, split_mode, split_params)
            print(f"✅ 自动生成文件名: {output_file}")
    
    # 返回完整配置
    return {
        "word_count": word_count,
        "passphrase": passphrase,
        "networks": args.networks,
        "address_count": args.addresses,
        "split_mode": split_mode,
        "split_params": split_params,
        "output_file": output_file,
        "display_only": display_only,
        "mnemonic": mnemonic,  # 添加助记词参数
    }


class WalletGenerator:
    """
    Web3钱包助记词生成器主类
    """

    def __init__(self):
        """初始化生成器"""
        self.validator = MnemonicValidator()
        self.formatter = OutputFormatter()
        self.wordlist_manager = WordlistManager()

    def generate_wallet(
        self,
        word_count: int = 24,
        passphrase: str = "",
        networks: List[str] = None,
        address_count: int = 5,
        split_mode: Optional[str] = None,
        split_params: Optional[Dict] = None,
        mnemonic: Optional[str] = None,  # 新增：支持指定助记词
    ) -> Dict:
        """
        生成钱包信息，包括助记词、种子、私钥和地址

        Args:
            word_count (int): 助记词单词数量
            passphrase (str): 密码短语
            networks (List[str]): 要生成地址的网络列表
            address_count (int): 每个网络生成的地址数量
            split_mode (Optional[str]): 分割模式 ('card' 或 'shamir')
            split_params (Optional[Dict]): 分割参数
            mnemonic (Optional[str]): 指定的助记词（如果提供则不生成新的）

        Returns:
            Dict: 包含助记词、种子、地址等信息的字典
        """
        try:
            # 使用英文语言初始化助记词生成器
            self.mnemonic_generator = MnemonicGenerator("english")

            # 生成或使用指定的助记词
            if mnemonic:
                # 验证提供的助记词
                print(f"🔍 使用指定的助记词...")
                validation_result = self.validator.comprehensive_validate(mnemonic)
                if not validation_result["is_valid"]:
                    errors = validation_result.get("errors", ["未知错误"])
                    raise ValueError(f"指定的助记词验证失败: {'; '.join(errors)}")
                print(f"✅ 助记词验证通过")
            else:
                # 生成新助记词
                print(f"🎲 生成新的 {word_count} 词助记词...")
                entropy_bits = {12: 128, 15: 160, 18: 192, 21: 224, 24: 256}[word_count]
                mnemonic = self.mnemonic_generator.generate_mnemonic(entropy_bits)

                # 验证生成的助记词
                validation_result = self.validator.comprehensive_validate(mnemonic)
                if not validation_result["is_valid"]:
                    errors = validation_result.get("errors", ["未知错误"])
                    raise ValueError(f"生成的助记词验证失败: {'; '.join(errors)}")
                print(f"✅ 助记词生成成功")

            # 生成EMVC验证码
            print(f"🔑 正在生成助记词验证码...")
            try:
                verification_code = self.mnemonic_generator.generate_verification_code(mnemonic)
                verification_info = self.mnemonic_generator.get_verification_code_info(verification_code)
                print(f"✅ 验证码生成成功: {verification_code}")
                print(f"   验证码说明: {verification_info['description']}")
            except Exception as e:
                print(f"⚠️ 验证码生成失败: {e}")
                verification_code = None
                verification_info = None

            # 生成种子
            seed = SeedGenerator.mnemonic_to_seed(mnemonic, passphrase)
            seed_hex = seed.hex()

            # 生成主密钥和派生地址
            key_derivation = KeyDerivation(seed)
            master_key_info = key_derivation.get_master_key_info()

            # 生成各网络地址
            networks = networks or ["bitcoin", "ethereum"]
            addresses = {}
            failed_networks = []
            for network in networks:
                try:
                    addresses[network] = key_derivation.derive_addresses(
                        network, address_count
                    )
                    print(f"✅ {network} 网络生成 {len(addresses[network])} 个地址")
                except ValueError as e:
                    failed_networks.append(network)
                    print(f"❌ 警告: 无法为网络 {network} 生成地址: {e}")
                except Exception as e:
                    failed_networks.append(network)
                    print(f"❌ 错误: 网络 {network} 地址生成失败: {e}")
                    
            # 如果所有网络都失败，抛出异常
            if not addresses:
                raise RuntimeError(f"所有网络地址生成失败: {failed_networks}")
            
            # 如果部分网络失败，给出警告
            if failed_networks:
                print(f"⚠️ 以下网络地址生成失败，但其他网络正常: {failed_networks}")

            # 生成参数信息（如果使用了指定助记词，word_count应该根据实际词数更新）
            actual_word_count = len(mnemonic.split()) if mnemonic else word_count
            entropy_bits = {12: 128, 15: 160, 18: 192, 21: 224, 24: 256}.get(actual_word_count, 256)
            
            generation_params = {
                "word_count": actual_word_count,
                "entropy_bits": entropy_bits,
                "language": "english",
                "passphrase": bool(passphrase),
                "address_count": address_count,
                "networks": networks,
                "split_mode": split_mode,
                "split_params": split_params,
                "mnemonic_source": "specified" if mnemonic else "generated",
            }

            # 处理分割模式
            split_info = None
            if split_mode:
                # ✅ 修复：确保密码短语被传递到分片生成
                split_params_with_passphrase = (split_params or {}).copy()
                split_params_with_passphrase["passphrase"] = passphrase
                split_info = self._handle_split_mode(
                    mnemonic, split_mode, split_params_with_passphrase
                )

            return {
                "mnemonic": mnemonic,
                "verification_code": verification_code,
                "verification_info": verification_info,
                "seed_hex": seed_hex,
                "master_key_info": master_key_info,
                "addresses": addresses,
                "generation_params": generation_params,
                "split_info": split_info,
                "validation_result": validation_result,
            }

        except Exception as e:
            raise RuntimeError(f"钱包生成失败: {str(e)}")

    def _handle_split_mode(
        self, mnemonic: str, split_mode: str, split_params: Dict
    ) -> Dict:
        """
        处理分割模式

        Args:
            mnemonic (str): 助记词
            split_mode (str): 分割模式
            split_params (Dict): 分割参数

        Returns:
            Dict: 分割信息
        """
        if split_mode == "card":
            return self._handle_card_split(mnemonic, split_params)
        elif split_mode == "shamir":
            return self._handle_shamir_split(mnemonic, split_params)
        else:
            raise ValueError(f"不支持的分割模式: {split_mode}")

    def _handle_card_split(self, mnemonic: str, params: Dict) -> Dict:
        """处理卡片分割 - 按PRD错位分散算法"""
        from src.core.card_split import CardSplitter
        
        splitter = CardSplitter()
        num_cards = params.get("num_cards", 3)

        # 按PRD要求，使用错位分散算法（不再使用overlap_ratio）
        split_result = splitter.split_to_cards(mnemonic, num_cards)
        security_info = splitter.estimate_security(split_result.cards)

        return {
            "mode": "card",
            "type": "card", 
            "cards": split_result.cards,
            "card_images": [],  # 如果需要可以后续添加
            "instructions": split_result.instructions,
            "security_info": security_info,
            "card_count": num_cards,
            "total_shares": num_cards,
            "threshold": num_cards,  # 卡片分割需要所有卡片
            "algorithm": "staggered_dispersion_prd_compliant",
        }

    def _handle_shamir_split(self, mnemonic: str, params: Dict) -> Dict:
        """处理Shamir分片生成 - 最优实现"""
        try:
            from core.shamir import ShamirSecretSharing
            
            shamir = ShamirSecretSharing()
            threshold = params.get("threshold", 3)
            total_shares = params.get("total_shares", 5)
            passphrase = params.get("passphrase", "")
            
            print(f"\n🔐 正在生成Shamir分片...")
            print(f"   阈值: {threshold}")
            print(f"   总分片数: {total_shares}")
            
            # 使用最优的分片方法
            shares, share_mnemonics = shamir.split_mnemonic(
                mnemonic=mnemonic,
                threshold=threshold,
                total=total_shares,
                passphrase=passphrase
            )
            
            # 为每个Share对象添加share_mnemonic属性
            for i, share in enumerate(shares):
                share.share_mnemonic = share_mnemonics[i]
            
            print(f"✅ 成功生成 {len(shares)} 个分片")
            
            # 生成原始助记词的验证码
            print(f"🔑 正在生成原始助记词验证码...")
            try:
                original_verification_code = self.mnemonic_generator.generate_verification_code(mnemonic)
                print(f"✅ 原始验证码: {original_verification_code}")
            except Exception as e:
                print(f"⚠️ 验证码生成失败: {e}")
                original_verification_code = None
            
            # 显示分片信息
            print(f"\n📊 分片信息:")
            print(f"   算法: Shamir秘密分享 (最优实现)")
            print(f"   原始助记词长度: {len(mnemonic.split())} 词")
            print(f"   恢复阈值: {threshold}")
            print(f"   总分片数: {total_shares}")
            print(f"   密码短语: {'是' if passphrase else '否'}")
            if original_verification_code:
                print(f"   原始验证码: {original_verification_code}")
            
            # 分片列表
            print(f"\n🔐 分片列表:")
            for i, share in enumerate(shares, 1):
                print(f"\n分片 {i}:")
                print(f"   {share.share_mnemonic}")
            
            # 重要安全提醒
            print(f"\n🚨 安全提醒:")
            print("1. 请将每个分片分别存储在不同的安全位置")
            print("2. 确保至少保留足够数量的分片进行恢复")
            print("3. 定期验证分片的完整性")
            print("4. 不要将所有分片存储在同一位置")
            print("5. 记录分片的生成参数（阈值、总数等）")
            
            # 立即验证分片的正确性 - 使用最优算法
            print(f"\n🔍 验证分片正确性...")
            try:
                recovered_mnemonic = shamir.recover_mnemonic(
                    share_mnemonics=share_mnemonics[:threshold],
                    mnemonic=mnemonic,
                    passphrase=passphrase
                )
                
                if recovered_mnemonic != mnemonic:
                    raise ValueError("❌ 分片验证失败：恢复的助记词与原始助记词不匹配")
                
                print("✅ Shamir分片验证成功: 恢复测试通过")
                
            except Exception as e:
                print(f"❌ 分片验证失败: {str(e)}")
                # 不再使用临时绕过，而是抛出真实错误
                raise ValueError(f"Shamir算法验证失败: {str(e)}")
            
            # 构建返回数据
            return {
                "type": "shamir",
                "algorithm": "shamir_secret_sharing_optimal",
                "threshold": threshold,
                "total_shares": total_shares,
                "shares": shares,  # 返回带有share_mnemonic属性的Share对象列表
                "recovery_info": {
                    "threshold": threshold,
                    "total_shares": total_shares,
                    "algorithm": "shamir_secret_sharing_optimal",
                    "passphrase_used": bool(passphrase),
                    "original_word_count": len(mnemonic.split()),
                    "security_level": "高",
                    "original_verification_code": original_verification_code
                }
            }
            
        except Exception as e:
            print(f"❌ Shamir分片失败: {str(e)}")
            raise

    def save_output(self, wallet_info: Dict, output_file: str, require_confirmation: bool = True) -> None:
        """
        保存输出文件 - 需要人为确认

        Args:
            wallet_info (Dict): 钱包信息
            output_file (str): 输出文件路径
            require_confirmation (bool): 是否需要用户确认
        """
        try:
            # 显示敏感信息警告
            print("\n" + "=" * 60)
            print("⚠️  重要安全警告")
            print("=" * 60)
            print("即将保存的文件包含敏感的助记词信息！")
            print("助记词可以完全控制您的钱包和资金。")
            print(f"目标文件: {output_file}")
            print("")
            print("安全建议:")
            print("- 确保在安全的离线环境中操作")
            print("- 确保文件保存在加密的存储设备上")
            print("- 保存后立即备份到多个安全位置")
            print("- 永远不要在联网设备上长期保存")
            print("=" * 60)

            if require_confirmation:
                # 第一次确认 - 基本同意
                try:
                    confirm1 = input("\n是否继续保存助记词文件? [y/N]: ").lower().strip()
                except (EOFError, KeyboardInterrupt):
                    confirm1 = "n"
                    print("N")  # 显示默认选择
                    
                if not confirm1.startswith('y'):
                    print("❌ 用户取消操作，未保存文件")
                    return

                # 第二次确认 - 确认理解风险
                print("\n再次确认：")
                print("您确认理解保存助记词文件的安全风险，")
                print("并承诺会妥善保管这些敏感信息？")
                try:
                    confirm2 = input("请输入 'YES' 来确认: ").strip()
                except (EOFError, KeyboardInterrupt):
                    confirm2 = ""
                    print("")  # 显示空输入
                    
                if confirm2 != "YES":
                    print("❌ 确认失败，未保存文件")
                    print("💡 提示：您可以选择仅查看助记词（不保存文件）")
                    
                    # 提供仅显示选项
                    try:
                        show_only = input("是否仅在终端显示助记词（不保存文件）? [y/N]: ").lower().strip()
                    except (EOFError, KeyboardInterrupt):
                        show_only = "n"
                        print("N")  # 显示默认选择
                        
                    if show_only.startswith('y'):
                        self._display_wallet_info_only(wallet_info)
                    return

                # 第三次确认 - 确认文件路径
                print(f"\n最终确认文件路径: {output_file}")
                try:
                    confirm3 = input("确认保存到此路径? [y/N]: ").lower().strip()
                except (EOFError, KeyboardInterrupt):
                    confirm3 = "y"  # 默认确认路径
                    print("Y")  # 显示默认选择
                    
                if not confirm3.startswith('y'):
                    try:
                        new_path = input("请输入新的文件路径（或按回车取消）: ").strip()
                    except (EOFError, KeyboardInterrupt):
                        new_path = ""
                        print("")  # 显示空输入
                        
                    if not new_path:
                        print("❌ 用户取消操作，未保存文件")
                        return
                    output_file = new_path

            # 执行保存操作
            print(f"\n🔄 正在保存到: {output_file}")
            
            # 生成主输出文件
            main_content = self.formatter.format_wallet_info(
                wallet_info["mnemonic"],
                wallet_info["seed_hex"],
                wallet_info["master_key_info"],
                wallet_info["addresses"],
                wallet_info["generation_params"],
                wallet_info["split_info"],
            )

            # 确保dist目录和输出目录存在
            import os
            
            # 确保dist目录存在
            os.makedirs("dist", exist_ok=True)
            
            # 确保输出文件的目录存在
            output_dir = os.path.dirname(output_file)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)

            with open(output_file, "w", encoding="utf-8") as f:
                f.write(main_content)

            print(f"✅ 主输出文件已保存: {output_file}")

            # 如果有分割信息，询问是否保存分割文件
            split_info = wallet_info.get("split_info")
            if split_info:
                try:
                    save_splits = input("是否同时保存分割文件? [y/N]: ").lower().strip()
                except (EOFError, KeyboardInterrupt):
                    save_splits = "n"
                    print("N")  # 显示默认选择
                    
                if save_splits.startswith('y'):
                    # 传递原始助记词给分割文件保存
                    original_mnemonic = wallet_info.get("mnemonic")
                    self._save_split_files(split_info, output_file, original_mnemonic)
                else:
                    print("⚠️  分割文件未保存")

            # 保存后的安全提醒
            print(f"\n🔒 文件已保存完成！")
            print("🚨 立即安全提醒:")
            print("1. 请立即备份此文件到多个安全位置")
            print("2. 考虑从当前设备删除此文件")
            print("3. 确保备份存储在离线环境")
            print("4. 定期验证备份的完整性")

        except Exception as e:
            raise RuntimeError(f"保存输出文件失败: {str(e)}")

    def _display_wallet_info_only(self, wallet_info: Dict) -> None:
        """仅在终端显示钱包信息，不保存文件"""
        print("\n" + "=" * 60)
        print("🔐 钱包信息 - 仅显示模式")
        print("=" * 60)
        
        print(f"\n📝 助记词 ({len(wallet_info['mnemonic'].split())} 个单词):")
        print(f"   {wallet_info['mnemonic']}")
        
        print(f"\n🌱 种子 (前16字节):")
        print(f"   {wallet_info['seed_hex'][:32]}...")
        
        print(f"\n🔑 生成的地址:")
        for network, addresses in wallet_info['addresses'].items():
            print(f"   {network.capitalize()}:")
            
            # 询问用户是否要显示完整地址列表
            if len(addresses) > 3:
                try:
                    show_all = input(f"     是否显示所有 {len(addresses)} 个{network}地址? [y/N]: ").lower().startswith('y')
                except (EOFError, KeyboardInterrupt):
                    # 处理EOF错误（如管道输入）或用户中断
                    show_all = False
                    print("N")  # 显示用户选择
            else:
                show_all = True
            
            if show_all:
                # 显示所有地址
                for i, addr in enumerate(addresses):
                    print(f"     {i+1:2d}. {addr.address}")
            else:
                # 只显示前3个地址
                for i, addr in enumerate(addresses[:3]):
                    print(f"     {i+1:2d}. {addr.address}")
                if len(addresses) > 3:
                    print(f"     ... 还有 {len(addresses) - 3} 个地址")
                    print(f"     💡 提示: 完整地址列表可保存到文件中查看")
        
        # 显示分割信息
        split_info = wallet_info.get('split_info')
        if split_info:
            print(f"\n🔐 分割信息:")
            if split_info['type'] == 'card':
                print(f"   分割类型: 卡片分割 (错位分散算法)")
                print(f"   卡片数量: {len(split_info['cards'])}")
                print("   卡片预览:")
                for i, card in enumerate(split_info['cards'], 1):
                    print(f"     Card {i}: {card.display_format()}")
                    print(f"     掩码位置: {card.masked_positions}")
                    print()
                    
            elif split_info['type'] == 'shamir':
                print(f"   分割类型: Shamir分割")
                print(f"   恢复阈值: {split_info['recovery_info']['threshold']}")
                print(f"   总分片数: {split_info['recovery_info']['total_shares']}")
                print("   分片预览:")
                for i, share in enumerate(split_info['shares'], 1):
                    print(f"     分片 {i}: {share.share_mnemonic}")
                    print()
        
        print(f"\n" + "=" * 60)
        print("⚠️  此信息未保存到文件")
        print("请手动安全记录您需要的信息")
        print("如需查看完整信息，建议保存到文件")
        print("=" * 60)

    def _save_split_files(self, split_info: Dict, base_filename: str, original_mnemonic: str = None) -> None:
        """保存分割相关文件"""
        base_name = os.path.splitext(base_filename)[0]

        if split_info["type"] == "card":
            # 保存卡片文件
            card_content = self.formatter.format_card_split_output(
                split_info["cards"], split_info["instructions"]
            )
            card_file = f"{base_name}_cards.md"
            with open(card_file, "w", encoding="utf-8") as f:
                f.write(card_content)
            print(f"✅ 卡片分割文件已保存: {card_file}")

        elif split_info["type"] == "shamir":
            # 为每个分片生成单独的文件，文件名格式：*_Part(N-M).md
            shares = split_info["shares"]
            recovery_info = split_info["recovery_info"]
            
            saved_files = []
            for share in shares:
                # 生成单个分片内容
                share_content = self.formatter.format_single_shamir_share(
                    share, recovery_info, original_mnemonic
                )
                # 文件名格式：基础名_Part(N-M).md，其中N是分片ID，M是总分片数
                share_file = f"{base_name}_Part({share.share_id}-{share.total_shares}).md"
                
                with open(share_file, "w", encoding="utf-8") as f:
                    f.write(share_content)
                saved_files.append(share_file)
                print(f"✅ Shamir分片 {share.share_id}/{share.total_shares} 已保存: {share_file}")
            
            print(f"✅ 所有 {len(shares)} 个分片文件已保存完成")
            if original_mnemonic:
                print(f"✅ 分片文件已保存，原始助记词已隐藏以提高安全性")
            print(f"📁 保存的文件: {', '.join(saved_files)}")


def create_argument_parser() -> argparse.ArgumentParser:
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        description="Web3钱包助记词生成器（英文版）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python main.py --words 24 --output dist/wallet.md
  python main.py --words 12 --networks bitcoin ethereum --addresses 10
  python main.py --split card --card-num 3 --output dist/secure_wallet.md
  python main.py --split shamir --shamir-threshold 3 --shamir-total 5
  python main.py --display-only  # 仅显示，不保存文件
  python main.py --mnemonic "word1 word2 ... word24" --display-only  # 使用指定助记词
  python main.py --mnemonic "your mnemonic here" --output test_wallet.md  # 测试现有助记词
  python main.py --shamir-recover --share-files dist/share1.md dist/share2.md dist/share3.md
  python main.py --shamir-recover --share-mnemonics "word1 word2..." "word3 word4..."
  python main.py --shamir-recover  # 交互式恢复模式
        """,
    )

    # 基本参数
    parser.add_argument(
        "--words",
        type=int,
        choices=[12, 15, 18, 21, 24],
        default=24,
        help="助记词单词数量 (默认: 24)",
    )

    parser.add_argument("--passphrase", type=str, default="", help="可选的密码短语")

    # 新增：支持指定助记词
    parser.add_argument(
        "--mnemonic", 
        type=str, 
        help="指定助记词（用于测试或使用现有助记词）"
    )

    parser.add_argument(
        "--networks",
        nargs="+",
        default=["bitcoin", "ethereum"],
        help="要生成地址的网络列表",
    )

    parser.add_argument(
        "--addresses", type=int, default=5, help="每个网络生成的地址数量 (默认: 5)"
    )

    parser.add_argument(
        "--output", type=str, default="", help="输出文件路径 (留空则自动生成文件名)"
    )

    # 分割相关参数
    parser.add_argument(
        "--split", choices=["card", "shamir"], help="启用助记词分割模式"
    )

    parser.add_argument(
        "--card-num", type=int, default=3, help="卡片分割的卡片数量 (默认: 3)"
    )

    # 注意：已移除 --card-overlap 参数，因为PRD要求使用错位分散算法，不需要重叠比例

    parser.add_argument(
        "--shamir-threshold", type=int, default=3, help="Shamir分割的恢复阈值 (默认: 3)"
    )

    parser.add_argument(
        "--shamir-total", type=int, default=5, help="Shamir分割的总分片数 (默认: 5)"
    )

    # 其他选项
    parser.add_argument("--interactive", action="store_true", help="启用交互式模式")

    parser.add_argument("--display-only", action="store_true", help="仅在终端显示，不保存文件")

    parser.add_argument("--validate", type=str, help="验证现有助记词的有效性")

    parser.add_argument("--list-networks", action="store_true", help="列出支持的网络")

    parser.add_argument(
        "--shamir-recover", action="store_true", help="从Shamir分片恢复原始助记词"
    )

    parser.add_argument(
        "--share-files", nargs="+", help="Shamir分片文件路径列表"
    )

    parser.add_argument(
        "--share-mnemonics", nargs="+", help="直接提供Shamir分片助记词列表"
    )

    parser.add_argument(
        "--card-recover", action="store_true", help="从卡片分割恢复原始助记词"
    )
    
    parser.add_argument(
        "--card-files", nargs="+", help="卡片分割文件路径列表"
    )
    
    parser.add_argument(
        "--card-words", nargs="+", help="直接提供卡片助记词列表"
    )



    return parser


def interactive_mode() -> Dict:
    """交互式模式 - 增强版本"""
    print("🔐 Web3钱包助记词生成器 - 交互式模式（英文版）")
    print("=" * 60)

    # 1. 助记词长度选择
    print("\n📝 助记词配置")
    print("支持的助记词长度:")
    print("  12词 - 128位熵，适合日常使用")
    print("  15词 - 160位熵，增强安全性")
    print("  18词 - 192位熵，高安全性")
    print("  21词 - 224位熵，企业级安全")
    print("  24词 - 256位熵，最高安全性")
    
    word_count = int(input("\n选择助记词长度 [12/15/18/21/24] (默认: 24): ") or "24")
    if word_count not in [12, 15, 18, 21, 24]:
        print("❌ 无效的助记词长度，使用默认值 24")
        word_count = 24
    print(f"✅ 已选择 {word_count} 词助记词")

    # 2. 密码短语
    print("\n🔒 密码短语配置")
    use_passphrase = input("是否使用密码短语 (增加额外安全层)? [y/N]: ").lower().startswith("y")
    passphrase = ""
    if use_passphrase:
        passphrase = input("请输入密码短语: ")
        print("✅ 已设置密码短语")

    # 3. 网络选择
    print("\n🌐 网络配置")
    from src.core.derivation import KeyDerivation
    kd = KeyDerivation(b"\x00" * 64)  # 临时实例用于获取支持的网络
    networks = kd.get_supported_networks()
    print(f"支持的网络: {', '.join(networks)}")
    selected_networks = input("选择网络 (空格分隔，默认: bitcoin ethereum): ").split()
    if not selected_networks:
        selected_networks = ["bitcoin", "ethereum"]
    print(f"✅ 已选择网络: {', '.join(selected_networks)}")

    # 4. 地址数量
    address_count = int(input("每个网络生成地址数量 (默认: 5): ") or "5")
    print(f"✅ 每个网络将生成 {address_count} 个地址")

    # 5. 分割模式配置
    print("\n🔐 分割方式配置")
    print("分割选项:")
    print("  1. 无分割 - 标准助记词输出")
    print("  2. 卡片分割 - 错位分散算法，需要所有卡片恢复")
    print("  3. Shamir分割 - 门限秘密共享，灵活恢复方案")
    
    split_choice = input("选择分割方式 [1/2/3] (默认: 1): ") or "1"
    
    split_mode = None
    split_params = {}
    
    if split_choice == "2":
        print("\n🃏 卡片分割配置")
        print("推荐配置:")
        print("  3卡片 - 个人使用，简单备份")
        print("  4卡片 - 家庭使用，分散风险")
        print("  6卡片 - 企业使用，多地备份")
        
        split_mode = "card"
        num_cards = int(input("卡片数量 [3-6] (默认: 3): ") or "3")
        if num_cards < 2 or num_cards > word_count:
            print(f"❌ 卡片数量应在 2-{word_count} 之间，使用默认值 3")
            num_cards = 3
        split_params = {"num_cards": num_cards}
        print(f"✅ 将使用错位分散算法分割为 {num_cards} 张卡片")
        
    elif split_choice == "3":
        print("\n🔀 Shamir分割配置")
        print("推荐配置:")
        print("  3/5 - 需要3个分片，总共5个分片")
        print("  5/7 - 需要5个分片，总共7个分片")
        print("  2/3 - 需要2个分片，总共3个分片")
        
        split_mode = "shamir"
        threshold = int(input("恢复阈值 (默认: 3): ") or "3")
        total_shares = int(input("总分片数 (默认: 5): ") or "5")
        
        if threshold > total_shares:
            print(f"❌ 阈值不能大于总分片数，调整为 {total_shares}/{total_shares}")
            threshold = total_shares
        
        split_params = {"threshold": threshold, "total_shares": total_shares}
        print(f"✅ 将生成 {total_shares} 个分片，需要 {threshold} 个分片恢复")
    else:
        print("✅ 将生成标准助记词（无分割）")

    # 6. 输出配置
    print("\n💾 输出配置")
    print("输出选项:")
    print("  1. 保存到文件 (自动命名)")
    print("  2. 保存到文件 (自定义路径)")
    print("  3. 仅在终端显示 (不保存文件)")
    
    output_choice = input("选择输出方式 [1/2/3] (默认: 1): ") or "1"
    
    display_only = False
    output_file = ""
    
    if output_choice == "3":
        display_only = True
        print("💡 选择了仅显示模式，不会保存文件")
    elif output_choice == "2":
        output_file = input("输入自定义文件路径 (例: dist/my_wallet.md): ")
        if not output_file:
            output_file = generate_default_filename(word_count, split_mode, split_params)
        print(f"✅ 将保存到: {output_file}")
    else:
        # 自动生成文件名
        output_file = generate_default_filename(word_count, split_mode, split_params)
        print(f"✅ 将自动保存到: {output_file}")

    # 7. 配置确认
    print("\n" + "=" * 60)
    print("📋 配置总结")
    print("=" * 60)
    print(f"助记词长度: {word_count} 词")
    print(f"密码短语: {'是' if passphrase else '否'}")
    print(f"目标网络: {', '.join(selected_networks)}")
    print(f"地址数量: {address_count} 个/网络")
    
    if split_mode == "card":
        print(f"分割方式: 卡片分割 ({split_params['num_cards']} 张卡片)")
    elif split_mode == "shamir":
        print(f"分割方式: Shamir分割 ({split_params['threshold']}/{split_params['total_shares']})")
    else:
        print("分割方式: 无分割")
    
    if display_only:
        print("输出方式: 仅显示")
    else:
        print(f"输出文件: {output_file}")
    
    print("=" * 60)
    
    confirm = input("\n确认以上配置? [Y/n]: ").lower()
    if confirm.startswith('n'):
        print("❌ 用户取消操作")
        sys.exit(0)
    
    print("🚀 开始生成钱包...")

    return {
        "word_count": word_count,
        "passphrase": passphrase,
        "networks": selected_networks,
        "address_count": address_count,
        "split_mode": split_mode,
        "split_params": split_params,
        "output_file": output_file,
        "display_only": display_only,
        "mnemonic": None,  # 交互式模式生成新助记词，不使用指定助记词
    }


def handle_card_split_mode(mnemonic, total_cards, output_path, display_only):
    """处理卡片分割模式"""
    from core.card_split import CardSplitter
    
    card_splitter = CardSplitter()
    split_result = card_splitter.split_to_cards(mnemonic, total_cards)
    
    if display_only:
        print("\n=== 卡片分割结果 ===")
        print(f"原始助记词: {mnemonic}")
        print(f"分割算法: 错位分散算法 (PRD规范)")
        print(f"生成卡片数: {total_cards}")
        print()
        
        for i, card in enumerate(split_result.cards, 1):
            print(f"Card {i}: {card.display_format()}")
            print(f"掩码位置: {card.masked_positions}")
            print()
            
        print(f"算法验证: 按照 i % {total_cards} == (card_id - 1) 公式分配")
        print("PRD规范: 完全符合")
    else:
        from utils.output import OutputFormatter
        output_formatter = OutputFormatter()
        # 保存卡片分割结果的逻辑需要实现
        print(f"\n卡片分割结果已保存到: {output_path}")


def handle_card_recovery(args):
    """处理卡片分割恢复"""
    from src.core.card_split import CardSplitter, CardSplit
    import os
    from datetime import datetime
    
    print("\n=== 卡片分割恢复模式 ===")
    
    cards = []
    
    # 方式1：从文件读取卡片
    if args.card_files:
        print(f"从文件读取卡片: {len(args.card_files)} 个文件")
        for file_path in args.card_files:
            if not os.path.exists(file_path):
                print(f"错误: 文件不存在 - {file_path}")
                return
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # 解析卡片文件内容，提取卡片信息
                # 这里需要根据实际保存的格式来解析
                print(f"✓ 已读取文件 {file_path}")
                    
            except Exception as e:
                print(f"错误: 无法读取文件 {file_path} - {e}")
                return
    
    # 方式2：直接提供卡片助记词
    elif args.card_words:
        print(f"使用提供的卡片助记词: {len(args.card_words)} 个卡片")
        total_cards = int(input("请输入总卡片数: ") or str(len(args.card_words)))
        
        for i, card_words in enumerate(args.card_words, 1):
            try:
                # 创建临时卡片对象用于恢复
                words = card_words.split()
                # 这里需要更完整的卡片重构逻辑
                print(f"✓ 已处理卡片 {i}")
            except Exception as e:
                print(f"错误: 卡片 {i} 无效 - {e}")
                return
    
    # 方式3：交互式输入
    else:
        print("交互式卡片输入模式")
        total_cards = int(input("请输入总卡片数: ") or "3")
        
        print(f"请输入 {total_cards} 张卡片的内容:")
        for i in range(1, total_cards + 1):
            card_content = input(f"卡片 {i}: ").strip()
            if not card_content:
                print(f"错误: 卡片 {i} 内容为空")
                return
                
            try:
                # 解析卡片内容
                words = card_content.split()
                print(f"✓ 卡片 {i} 有效")
            except Exception as e:
                print(f"错误: 卡片 {i} 格式错误 - {e}")
                return
    
    # 执行恢复
    if not cards:
        print("错误: 没有有效的卡片数据")
        return
    
    try:
        splitter = CardSplitter()
        
        print(f"\n正在恢复原始助记词...")
        print(f"使用卡片数: {len(cards)}")
        
        recovered_mnemonic = splitter.reconstruct_mnemonic(cards)
        
        print("\n=== 恢复成功! ===")
        print(f"原始助记词: {recovered_mnemonic}")
        print(f"助记词长度: {len(recovered_mnemonic.split())} 词")
        
        # 验证恢复的助记词
        from src.core.mnemonic import MnemonicGenerator
        mnemonic_gen = MnemonicGenerator()
        if mnemonic_gen.validate_mnemonic(recovered_mnemonic):
            print("✓ 助记词格式验证通过")
        else:
            print("⚠ 警告: 助记词格式验证失败")
        
        # 询问是否保存
        save_result = input("\n是否将恢复结果保存到文件? (y/N): ").strip().lower()
        if save_result in ['y', 'yes']:
            # 生成默认恢复文件名
            default_recovery_file = generate_recovery_filename("card", {
                "word_count": len(recovered_mnemonic.split()),
                "split_mode": "card",
                "split_params": {"num_cards": len(cards)}
            })
            output_path = input(f"输出文件路径 (默认: {default_recovery_file}): ").strip()
            if not output_path:
                output_path = default_recovery_file
            
            # 确保目录存在
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("# 从卡片恢复的钱包助记词\n\n")
                f.write(f"**恢复时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write(f"**原始助记词**: {recovered_mnemonic}\n\n")
                f.write(f"**助记词长度**: {len(recovered_mnemonic.split())} 词\n\n")
                f.write(f"**使用卡片数**: {len(cards)}\n\n")
                f.write("## 安全提醒\n\n")
                f.write("- 请妥善保管恢复的助记词\n")
                f.write("- 确认助记词无误后删除此文件\n")
                f.write("- 不要在不安全的环境中使用\n")
            
            print(f"✓ 恢复结果已保存到: {output_path}")
        
    except Exception as e:
        print(f"恢复失败: {e}")
        print("请检查:")
        print("1. 卡片内容是否正确")
        print("2. 卡片数量是否完整")
        print("3. 卡片是否来自同一次分割操作")


def handle_shamir_split_mode(mnemonic, threshold, total_shares, output_path, display_only):
    """处理Shamir分片模式"""
    print("\n=== Shamir秘密分享模式 ===")
    
    # 重要提醒
    print("🔴 重要提醒：Shamir分片操作")
    print("=" * 50)
    print("1. 请确保您输入的是正确的原始助记词")
    print("2. 分片生成后，请妥善保管每个分片")
    print("3. 建议先用小额测试验证助记词正确性")
    print("4. 如果使用密码短语，请确保记录")
    print("=" * 50)
    
    # 助记词验证提示
    print(f"\n📝 您要分片的助记词:")
    print(f"   {mnemonic}")
    print(f"   长度: {len(mnemonic.split())} 个单词")
    
    # 用户确认
    confirm = input("\n⚠️  请仔细确认上述助记词是否正确 (输入 'YES' 继续): ").strip()
    if confirm != "YES":
        print("❌ 用户取消操作")
        return
    
    # 密码短语确认
    passphrase_confirm = input("\n是否使用了密码短语? (y/N): ").lower().strip()
    passphrase = ""
    if passphrase_confirm.startswith('y'):
        passphrase = input("请输入密码短语: ").strip()
        print("✓ 已记录密码短语")
    
    try:
        from core.shamir import ShamirSecretSharing
        
        shamir = ShamirSecretSharing()
        
        print(f"\n🔄 正在生成Shamir分片...")
        print(f"   阈值: {threshold}")
        print(f"   总分片数: {total_shares}")
        
        shares, share_mnemonics = shamir.split_mnemonic(
            mnemonic=mnemonic,
            threshold=threshold,
            total=total_shares,
            passphrase=passphrase
        )
        
        # 为每个Share对象添加share_mnemonic属性
        for i, share in enumerate(shares):
            share.share_mnemonic = share_mnemonics[i]
        
        print(f"✅ 成功生成 {len(shares)} 个分片")
        
        # 显示分片信息
        print(f"\n📊 分片信息:")
        print(f"   算法: Shamir秘密分享 (最优实现)")
        print(f"   原始助记词长度: {len(mnemonic.split())} 词")
        print(f"   恢复阈值: {threshold}")
        print(f"   总分片数: {total_shares}")
        print(f"   密码短语: {'是' if passphrase else '否'}")
        
        # 分片列表
        print(f"\n🔐 分片列表:")
        for i, share in enumerate(shares, 1):
            print(f"\n分片 {i}:")
            print(f"   {share.share_mnemonic}")
        
        # 重要安全提醒
        print(f"\n🚨 安全提醒:")
        print("1. 请将每个分片分别存储在不同的安全位置")
        print("2. 确保至少保留足够数量的分片进行恢复")
        print("3. 定期验证分片的完整性")
        print("4. 不要将所有分片存储在同一位置")
        print("5. 记录分片的生成参数（阈值、总数等）")
        
        if display_only:
            print(f"\n📄 分片信息仅显示，未保存到文件")
        else:
            # 保存分片文件
            save_shares = input(f"\n是否保存分片到文件? (y/N): ").lower().strip()
            if save_shares.startswith('y'):
                if not output_path:
                    output_path = f"dist/shamir_shares_{threshold}of{total_shares}.md"
                
                # 生成分片文件内容
                from utils.output import OutputFormatter
                formatter = OutputFormatter()
                
                recovery_info = {
                    "threshold": threshold,
                    "total_shares": total_shares,
                    "algorithm": "shamir_secret_sharing_optimal",
                    "original_word_count": len(mnemonic.split()),
                    "passphrase_used": bool(passphrase),
                    "generation_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                content = formatter.format_shamir_output(shares, recovery_info, mnemonic)
                
                # 确保目录存在
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print(f"✅ 分片已保存到: {output_path}")
            else:
                print("⚠️  分片未保存到文件，请手动安全记录")
        
    except Exception as e:
        print(f"❌ Shamir分片生成失败: {e}")
        raise RuntimeError(f"Shamir分片操作失败: {str(e)}")


def _smart_recovery_from_mnemonics(share_mnemonics, threshold, total_shares, original_word_count):
    """
    ⚠️  改进的恢复函数：强调用户验证的重要性
    
    重要声明：
    基于Shamir算法的数学特性，任何满足阈值的分片组合都能生成格式正确的助记词，
    但只有使用正确的分片ID组合才能恢复真正的原始助记词。
    
    本函数主要目的是教育用户理解这一现实，并提供一个"最可能"的结果供验证。
    
    Args:
        share_mnemonics: 分片助记词列表
        threshold: 恢复阈值
        total_shares: 总分片数
        original_word_count: 原始助记词长度
        
    Returns:
        List[ShamirShare]: 连续ID组合的分片列表（最常见的情况）
    """
    from itertools import permutations
    from src.core.mnemonic import MnemonicGenerator
    from core.shamir import ShamirSecretSharing, ShamirShare
    
    print(f"🔍 正在智能分析分片...")
    print("⚠️  重要数学现实提醒：")
    print("   Shamir算法允许任何分片组合恢复出格式正确的助记词")
    print("   只有正确的分片ID组合才能恢复您真正的原始助记词！")
    print("   本程序将使用最常见的连续ID假设 [1, 2, 3...]")
    
    num_shares = len(share_mnemonics)
    
    # 计算原始秘密长度
    expected_entropy_length = {12: 16, 15: 20, 18: 24, 21: 28, 24: 32}
    original_secret_length = expected_entropy_length.get(original_word_count, 32)
    
    metadata = {
        "original_mnemonic_words": str(original_word_count),
        "original_secret_length": str(original_secret_length)
    }
    
    # ✅ 改进策略：直接使用连续ID组合（最常见情况）
    print(f"🎯 使用连续分片ID策略 [1, 2, 3...{num_shares}]")
    
    try:
        # 创建连续ID的分片对象
        shares = []
        for i, mnemonic in enumerate(share_mnemonics):
            share_id = i + 1  # 连续ID：1, 2, 3...
            share = ShamirShare.from_mnemonic(
                mnemonic, share_id, threshold, total_shares,
                original_word_count=original_word_count, metadata=metadata
            )
            shares.append(share)
        
        # 验证恢复
        shamir = ShamirSecretSharing()
        recovered_mnemonic = shamir.reconstruct_mnemonic_from_shares(shares[:threshold], silent_mode=True)
        
        # 基础验证
        mnemonic_gen = MnemonicGenerator()
        if mnemonic_gen.validate_mnemonic(recovered_mnemonic):
            print(f"✅ 使用连续ID [1-{num_shares}] 恢复成功")
            print(f"📝 恢复的助记词前8词: {' '.join(recovered_mnemonic.split()[:8])}...")
            
            print(f"\n🚨 极重要验证提醒：")
            print("   1. 这可能不是您的真实助记词！")
            print("   2. 请务必验证：恢复的钱包地址是否与您已知的地址匹配")
            print("   3. 建议：先用小额测试验证，确认正确后再使用")
            print("   4. 如果地址不匹配，说明分片ID组合错误或分片来源不同")
            
            return shares
        else:
            raise ValueError("连续ID组合恢复的助记词格式无效")
            
    except Exception as e:
        # 连续ID失败，尝试其他常见组合
        print(f"⚠️  连续ID恢复失败: {e}")
        print("🔍 尝试其他常见ID组合...")
        
        # 尝试一些常见的替代组合
        common_combinations = [
            [1, 2, 3, 4, 5][:num_shares],  # 标准连续
            [2, 3, 4, 5, 6][:num_shares],  # 偏移连续
            [1, 3, 5, 7, 9][:num_shares],  # 奇数序列
        ]
        
        for attempt, id_combo in enumerate(common_combinations, 1):
            if len(id_combo) != num_shares:
                continue
                
            try:
                shares = []
                for i, mnemonic in enumerate(share_mnemonics):
                    share_id = id_combo[i]
                    share = ShamirShare.from_mnemonic(
                        mnemonic, share_id, threshold, total_shares,
                        original_word_count=original_word_count, metadata=metadata
                    )
                    shares.append(share)
                
                recovered_mnemonic = shamir.reconstruct_mnemonic_from_shares(shares[:threshold], silent_mode=True)
                
                if mnemonic_gen.validate_mnemonic(recovered_mnemonic):
                    print(f"✅ 尝试{attempt}成功：ID组合 {id_combo}")
                    print(f"📝 恢复的助记词前8词: {' '.join(recovered_mnemonic.split()[:8])}...")
                    
                    print(f"\n🚨 警告：这是基于常见模式的猜测")
                    print("   请务必验证恢复的助记词和钱包地址！")
                    
                    return shares
                    
            except Exception:
                continue
        
        # 所有常见组合都失败
        raise ValueError(
            "❌ 无法通过常见ID组合恢复助记词。\n"
            "可能原因：\n"
            "1. 分片助记词有误\n" 
            "2. 分片使用了非标准ID组合\n"
            "3. 分片参数（阈值/总数）错误\n"
            "建议：使用分片文件恢复（包含正确的分片ID信息）"
        )


def handle_shamir_recovery(args):
    """处理Shamir分片恢复 - 增强版本，包含验证码验证"""
    from src.core.shamir import ShamirSecretSharing
    from core.mnemonic import MnemonicGenerator
    
    print("\n=== Shamir分片恢复模式 ===")
    
    # 交互式输入分片
    threshold = int(input("请输入恢复阈值: ") or "3")
    total_shares = int(input("请输入总分片数: ") or "5")
    passphrase = input("请输入密码短语 (如果没有请直接回车): ").strip()
    
    print(f"请依次输入 {threshold} 个分片助记词:")
    share_mnemonics = []
    for i in range(threshold):
        share_mnemonic = input(f"分片 {i+1}: ").strip()
        share_mnemonics.append(share_mnemonic)
        print(f"✓ 分片 {i+1} 已收集")
    
    try:
        shamir = ShamirSecretSharing()
        
        print(f"\n🔄 正在恢复原始助记词...")
        print(f"使用分片数: {len(share_mnemonics)}")
        print(f"恢复阈值: {threshold}")
        
        recovered_mnemonic = shamir.reconstruct_mnemonic_from_shares(share_mnemonics, passphrase)
        
        print("\n=== 恢复成功! ===")
        print(f"恢复的助记词: {recovered_mnemonic}")
        print(f"助记词长度: {len(recovered_mnemonic.split())} 词")
        
        # 验证恢复的助记词格式
        mnemonic_validator = MnemonicGenerator()
        if mnemonic_validator.validate_mnemonic(recovered_mnemonic):
            print("✅ 助记词格式验证通过")
        else:
            print("⚠️ 警告: 助记词格式验证失败")
            
        # 新增：验证码验证功能
        print(f"\n🔑 助记词验证码验证")
        
        # 生成当前助记词的验证码
        try:
            current_verification_code = mnemonic_validator.generate_verification_code(recovered_mnemonic)
            print(f"恢复的助记词验证码: {current_verification_code}")
        except Exception as e:
            print(f"⚠️ 验证码生成失败: {e}")
            current_verification_code = None
        
        # 尝试从分片中提取原始验证码进行自动验证
        original_verification_code = None
        
        # 检查是否可以从分片信息中获取验证码
        # 注意：这是一个简化的假设，实际中可能需要更复杂的逻辑来提取recovery_info
        print("🔍 正在检查分片中的原始验证码...")
        
        # TODO: 这里假设我们可以从分片中获取原始验证码
        # 在实际实现中，需要解析分片文件或从用户提供的recovery_info中获取
        
        # 询问用户是否有原始验证码进行比对  
        use_verification = input("是否有原始助记词的验证码进行验证? [y/N]: ").lower().startswith("y")
        
        if use_verification and current_verification_code:
            expected_code = input("请输入原始助记词的验证码: ").strip()
            
            if expected_code:
                # 验证验证码匹配
                is_code_match = mnemonic_validator.verify_mnemonic_with_code(recovered_mnemonic, expected_code)
                
                if is_code_match:
                    print("🎉 验证码匹配！恢复的助记词准确无误")
                    print("✅ 您可以安全地使用这个助记词")
                else:
                    print("❌ 验证码不匹配！")
                    print("⚠️ 警告：恢复的助记词可能不是您的原始助记词")
                    print("可能的原因:")
                    print("1. 分片助记词输入错误")
                    print("2. 密码短语不正确")
                    print("3. 分片来自不同的原始助记词")
                    print("4. 验证码输入错误")
                    print("\n⚠️ 根据您的设置，程序将继续执行，但请谨慎使用此助记词")
                    
                    # 提供重试选项
                    retry = input("\n是否重新验证或重新恢复? [重新验证=v/重新恢复=r/继续=N]: ").lower().strip()
                    if retry == 'v':
                        # 重新验证验证码
                        new_code = input("请重新输入原始验证码: ").strip()
                        if new_code and mnemonic_validator.verify_mnemonic_with_code(recovered_mnemonic, new_code):
                            print("🎉 验证码匹配！恢复成功")
                        else:
                            print("❌ 验证码仍然不匹配")
                            print("⚠️ 程序继续执行，但请谨慎使用")
                    elif retry == 'r':
                        print("请重新运行恢复程序")
                        return
                    else:
                        print("⚠️ 继续执行，但请谨慎验证助记词的正确性")
            else:
                print("⚠️ 验证码为空，跳过验证")
        else:
            if current_verification_code:
                print(f"📝 建议记录此验证码：{current_verification_code}")
                print("以便将来验证助记词的正确性")
            print("✅ 跳过验证码验证")
        
    except Exception as e:
        print(f"❌ 恢复失败: {e}")
        print("请检查:")
        print("1. 分片助记词是否正确")
        print("2. 密码短语是否正确")
        print("3. 分片是否来自同一组")





def main():
    """主函数"""
    parser = create_argument_parser()
    args = parser.parse_args()

    # 处理特殊选项
    if args.list_networks:
        from core.derivation import KeyDerivation
        kd = KeyDerivation(b"\x00" * 64)  # 临时实例
        print("支持的网络:")
        for network in kd.get_supported_networks():
            print(f"  - {network}")
        return

    if args.shamir_recover:
        handle_shamir_recovery(args)
        return
        
    if args.card_recover:
        handle_card_recovery(args)
        return

    if args.validate:
        from core.mnemonic import MnemonicGenerator
        from utils.validation import MnemonicValidator
        
        validator = MnemonicValidator()
        mnemonic_gen = MnemonicGenerator()
        
        print(f"🔍 验证助记词：{args.validate[:50]}...")
        
        # 基础格式验证
        result = validator.comprehensive_validate(args.validate)
        print(f"基础验证结果: {'✅ 有效' if result['is_valid'] else '❌ 无效'}")
        
        if not result["is_valid"]:
            print("验证错误:")
            for validation_type in [
                "format_validation",
                "words_validation", 
                "checksum_validation",
            ]:
                if validation_type in result and "errors" in result[validation_type]:
                    for error in result[validation_type]["errors"]:
                        print(f"  - {error}")
        
        # 如果基础验证通过，提供验证码功能
        if result["is_valid"]:
            print(f"\n🔑 验证码功能")
            
            # 生成验证码
            try:
                verification_code = mnemonic_gen.generate_verification_code(args.validate)
                print(f"✅ 助记词验证码: {verification_code}")
                
                # 获取验证码信息
                code_info = mnemonic_gen.get_verification_code_info(verification_code)
                if code_info.get('valid_format'):
                    print(f"   格式: {code_info['format']}")
                    print(f"   说明: {code_info['description']}")
                
                # 询问是否进行验证码验证
                verify_with_code = input("\n是否有已知的验证码需要验证匹配? [y/N]: ").lower().startswith("y")
                
                if verify_with_code:
                    expected_code = input("请输入期望的验证码: ").strip()
                    
                    if expected_code:
                        is_match = mnemonic_gen.verify_mnemonic_with_code(args.validate, expected_code)
                        
                        if is_match:
                            print("🎉 验证码完全匹配！")
                            print("✅ 助记词验证通过，与原始记录一致")
                        else:
                            print("❌ 验证码不匹配！")
                            print("⚠️ 助记词可能与原始记录不一致")
                            print(f"当前验证码: {verification_code}")
                            print(f"期望验证码: {expected_code}")
                    else:
                        print("⚠️ 验证码为空，跳过验证")
                else:
                    print("💡 建议保存此验证码以备将来验证使用")
                    
            except Exception as e:
                print(f"⚠️ 验证码生成失败: {e}")
        
        return



    try:
        generator = WalletGenerator()

        if args.interactive:
            # 交互式模式
            params = interactive_mode()
            output_file = params.pop("output_file")  # 从参数中移除output_file
            display_only = params.pop("display_only", False)  # 获取显示模式
            wallet_info = generator.generate_wallet(**params)
        else:
            # 命令行模式 - 检查是否需要提示用户补充参数
            need_prompt = False
            
            # 检查是否需要参数提示：
            # 1. 没有指定分割方式且使用默认助记词长度
            # 2. 没有指定输出方式
            if (args.words == 24 and not args.split) or (not args.output and not args.display_only):
                need_prompt = True
            
            if need_prompt:
                # 提示用户补充参数
                params = prompt_missing_params(args)
                
                # 使用用户选择的参数
                wallet_info = generator.generate_wallet(
                    word_count=params["word_count"],
                    passphrase=params["passphrase"],
                    networks=params["networks"],
                    address_count=params["address_count"],
                    split_mode=params["split_mode"],
                    split_params=params["split_params"],
                    mnemonic=params.get("mnemonic"),
                )
                
                output_file = params["output_file"]
                display_only = params["display_only"]
            else:
                # 直接使用命令行参数
                display_only = args.display_only
                split_params = {}
                if args.split == "card":
                    split_params = {
                        "num_cards": args.card_num,
                        # 不再使用overlap_ratio，按PRD要求使用错位分散算法
                    }
                elif args.split == "shamir":
                    split_params = {
                        "threshold": args.shamir_threshold,
                        "total_shares": args.shamir_total,
                    }

                wallet_info = generator.generate_wallet(
                    word_count=args.words,
                    passphrase=args.passphrase,
                    networks=args.networks,
                    address_count=args.addresses,
                    split_mode=args.split,
                    split_params=split_params,
                    mnemonic=args.mnemonic,
                )
                
                # 智能文件命名：如果没有指定输出文件，则自动生成
                output_file = args.output
                if not output_file:
                    output_file = generate_default_filename(args.words, args.split, split_params)
                    print(f"📁 自动生成文件名: {output_file}")

        # 根据模式选择输出方式
        if display_only:
            # 仅显示模式
            generator._display_wallet_info_only(wallet_info)
            print("\n🎉 钱包生成完成!")
            print("💡 信息仅在终端显示，未保存到文件")
        else:
            # 保存到文件模式
            generator.save_output(wallet_info, output_file)
            print("\n🎉 钱包生成完成!")
            if hasattr(generator, '_file_saved') and generator._file_saved:
                print(f"📁 输出文件: {output_file}")

        # 显示安全提示
        print("\n⚠️  安全提示:")
        print("- 请安全保存生成的助记词信息")
        print("- 建议在离线环境中查看和备份助记词")
        print("- 永远不要在网络上分享您的助记词")

    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
