# 🔐 WalletX - Web3钱包助记词生成器

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![BIP-39](https://img.shields.io/badge/BIP--39-compliant-green.svg)](https://github.com/bitcoin/bips/blob/master/bip-0039.mediawiki)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**WalletX** 是一个专业的 Web3 钱包助记词生成器，完全符合 BIP-39/BIP-32/BIP-44 标准。项目提供了独创的助记词验证码系统和高级分片技术，为您的数字资产安全保驾护航。

## ✨ 核心特色

### 🎯 **独创技术**
- **🔑 EMVC验证码系统**：为助记词生成唯一验证码，确保备份完整性
- **🧩 优化Shamir分片**：16字节块技术，数学安全，生产级可靠性
- **🃏 智能卡片分割**：错位分散算法，单卡无法恢复完整信息

### 🛡️ **安全保障**
- **🔒 密码学安全**：CSPRNG随机数生成，多层SHA-256哈希
- **✅ 标准兼容**：100% 符合 BIP-39/32/44 国际标准
- **🔍 完整性验证**：验证码自动检测助记词篡改
- **💾 内存安全**：敏感数据用后即清，避免内存泄漏

### 🚀 **功能丰富**
- **📱 多链支持**：Bitcoin、Ethereum、Binance Chain 等 10+ 主流网络
- **🎲 灵活生成**：支持 12/15/18/21/24 词助记词
- **📊 批量派生**：一键生成多个地址和私钥
- **📄 专业输出**：Markdown 格式，清晰美观

## 🎮 快速开始

### 安装依赖

```bash
# 克隆项目
git clone https://github.com/0x0059/WalletX.git
cd WalletX

# 安装依赖
pip install -r requirements/base.txt
```

### 基础使用

```bash
# 🎲 生成24词助记词（推荐）
python src/main.py --words 24

# 🔍 验证现有助记词
python src/main.py --validate "your mnemonic words here"

# 📋 查看支持的网络
python src/main.py --list-networks

# 💡 交互式模式（新手推荐）
python src/main.py --interactive
```

## 📚 详细功能

### 🔑 验证码功能（EMVC）

为您的助记词生成唯一验证码，确保备份安全：

```bash
# 生成助记词和验证码
python src/main.py --words 12

# 输出示例：
# 助记词: abandon abandon abandon...
# 验证码: 9911-GRNQ
```

**验证码用途**：
- 📝 备份时记录验证码
- 🔍 恢复时验证助记词正确性
- 🛡️ 检测助记词是否被篡改

### 🧩 Shamir分片技术

将助记词安全分割成多个分片，增强安全性：

```bash
# 创建3-of-5分片（需要3个分片即可恢复）
python src/main.py --words 24 --split shamir --shamir-threshold 3 --shamir-total 5

# 从分片恢复助记词
python src/main.py --shamir-recover
```

**分片优势**：
- 🔐 单个分片无法恢复完整助记词
- 🌍 分片可分散存储在不同地点
- 📊 数学安全，经过严格验证

### 🃏 卡片分割

将助记词分散到多张卡片，适合物理存储：

```bash
# 创建3张卡片分割
python src/main.py --words 18 --split card --card-num 3

# 从卡片恢复
python src/main.py --card-recover
```

## 🌐 支持的区块链网络

| 网络 | 符号 | 地址类型 |
|------|------|----------|
| Bitcoin | BTC | Legacy, SegWit |
| Ethereum | ETH | ERC-20 compatible |
| Binance Smart Chain | BNB | BEP-20 compatible |
| Litecoin | LTC | Standard |
| Dogecoin | DOGE | Standard |
| Bitcoin Cash | BCH | Standard |
| Cardano | ADA | Standard |
| Polkadot | DOT | Standard |
| Solana | SOL | Standard |
| Avalanche | AVAX | Standard |

## 📖 高级用法

### 批量生成地址

```bash
# 为多个网络生成地址
python src/main.py --words 24 --networks bitcoin ethereum binance --addresses 10

# 使用密码短语增强安全性
python src/main.py --words 24 --passphrase --output secure_wallet.md
```

### 恢复和验证

```bash
# Shamir分片恢复（带验证码验证）
python src/main.py --shamir-recover --share-files share1.md share2.md share3.md

# 验证助记词并检查验证码
python src/main.py --validate "your mnemonic" --verification-code "1234-ABCD"
```

## ⚠️ 安全提醒

### 🔒 **助记词安全**
- ✅ **离线生成**：建议在断网环境中使用
- ✅ **多重备份**：物理备份 + 数字备份
- ✅ **分散存储**：不要将所有备份放在同一地点
- ❌ **避免数字存储**：不要保存在云盘、邮箱等联网位置

### 🔑 **验证码管理**
- ✅ **分开保存**：验证码与助记词分开存储
- ✅ **定期验证**：定期使用验证码检查备份完整性
- ✅ **记录清晰**：确保验证码记录清晰可读

### 🧩 **分片安全**
- ✅ **地理分散**：将分片存储在不同地理位置
- ✅ **可信保管**：选择可信的人或机构保管分片
- ✅ **定期测试**：定期测试分片恢复流程

## 🛠️ 技术架构

### 核心模块

```
src/
├── core/                    # 核心算法
│   ├── entropy.py          # 熵生成和校验和
│   ├── mnemonic.py         # BIP-39助记词 + EMVC验证码
│   ├── verification.py     # EMVC验证码系统
│   ├── shamir.py           # Shamir秘密分享（16字节块）
│   ├── card_split.py       # 卡片分割（错位分散）
│   ├── derivation.py       # BIP-32/44密钥派生
│   └── seed.py             # PBKDF2种子生成
├── utils/                   # 工具模块
│   ├── wordlists.py        # BIP-39词表管理
│   ├── validation.py       # 助记词验证
│   └── output.py           # Markdown输出格式化
└── bip39/                   # 官方BIP-39词表
    └── english.txt         # 2048个标准英语词汇
```

### 算法特色

- **🔬 EMVC验证码**：64位熵空间，XXXX-YYYY 人性化格式
- **🧮 16字节Shamir**：解决传统32字节块溢出问题
- **🔄 错位分散卡片**：基于模运算的智能掩码分布

## 📊 性能指标

| 操作 | 性能要求 | 实际表现 |
|------|----------|----------|
| 助记词生成 | < 200ms | ✅ ~100ms |
| 验证码生成 | < 50ms | ✅ ~20ms |
| Shamir分片 | < 1s | ✅ ~500ms |
| 地址派生(10个) | < 500ms | ✅ ~300ms |
| 内存占用 | < 50MB | ✅ ~20MB |

## 🔧 开发指南

### 环境要求

- **Python**: 3.8+
- **操作系统**: Windows 10+, macOS 10.15+, Linux
- **内存**: 最低 512MB，推荐 1GB

### 依赖管理

```bash
# 开发环境
pip install -r requirements/dev.txt

# 生产环境
pip install -r requirements/base.txt
```

### 代码风格

项目遵循 Python 最佳实践：

- **类型注解**：使用类型提示增强代码可读性
- **文档注释**：JSDoc 风格的详细注释
- **错误处理**：优雅的异常处理和用户提示
- **安全编程**：防御性编程，假设输入不可信

## 🤝 贡献指南

我们欢迎社区贡献！请遵循以下准则：

1. **🍴 Fork 项目**并创建功能分支
2. **✅ 确保测试通过**并添加必要的测试
3. **📝 更新文档**，包括代码注释和用户文档
4. **🔍 遵循代码风格**，运行 `black` 格式化代码
5. **📤 提交 Pull Request**，详细描述改动内容

### 报告问题

如发现 Bug 或有功能建议，请：

1. 🔍 **搜索现有 Issue** 避免重复
2. 📝 **详细描述问题** 包括重现步骤
3. 🖼️ **提供截图或日志** 帮助定位问题
4. 🏷️ **添加适当标签** 如 bug、enhancement 等

## 📄 许可证

本项目基于 MIT 许可证开源。详见 [LICENSE](LICENSE) 文件。

## 🙏 致谢

- **Bitcoin BIP-39**: [官方标准规范](https://github.com/bitcoin/bips/blob/master/bip-0039.mediawiki)
- **iancoleman/bip39**: [参考实现](https://github.com/iancoleman/bip39)
- **Shamir秘密分享**: Adi Shamir 的开创性算法
- **开源社区**: 感谢所有贡献者和使用者

## 📞 联系我们

- **项目主页**: [WalletX GitHub](https://github.com/0x0059/WalletX)
- **技术文档**: [PRD文档](docs/PRD.md)
- **问题反馈**: [GitHub Issues](https://github.com/0x0059/WalletX/issues)

---

**⚠️ 免责声明**: 本工具仅供学习和研究使用。用户须自行承担使用风险，开发者不对任何资产损失承担责任。请确保在安全环境中使用，妥善保管生成的助记词和私钥。

**🔐 安全提醒**: 助记词是您数字资产的唯一凭证，一旦丢失将无法找回。请务必做好安全备份，切勿与他人分享。 