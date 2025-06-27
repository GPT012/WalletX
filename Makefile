# WalletX Makefile - 精简版

.PHONY: help install dev test lint format clean

help:  ## 显示帮助信息
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

install:  ## 安装项目依赖
	pip install -e .

dev:  ## 安装开发依赖
	pip install -e .[dev]

test:  ## 运行测试
	python -m pytest tests/ -v

lint:  ## 代码检查
	python -m flake8 src/ tests/

format:  ## 代码格式化
	python -m black src/ tests/

clean:  ## 清理临时文件
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf *.egg-info/
	rm -rf build/
	rm -rf dist/ 