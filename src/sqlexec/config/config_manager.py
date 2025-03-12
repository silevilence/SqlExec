import os
import toml
import logging
from pathlib import Path
from typing import Dict, Any

class ConfigManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config_dir = Path.home() / ".sqlexec"
        self.config_file = self.config_dir / "config.toml"
        self.default_config_file = Path(__file__).parent / "default_config.toml"

    def load_config(self) -> Dict[str, Any]:
        """加载配置文件，如果不存在则创建默认配置"""
        try:
            if not self.config_file.exists():
                self._create_default_config()
            
            return toml.load(self.config_file)
        except Exception as e:
            self.logger.error(f"加载配置文件失败: {e}")
            return self._load_default_config()

    def save_config(self, config: Dict[str, Any]) -> bool:
        """保存配置到文件"""
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, "w", encoding="utf-8") as f:
                toml.dump(config, f)
            return True
        except Exception as e:
            self.logger.error(f"保存配置文件失败: {e}")
            return False

    def _create_default_config(self) -> None:
        """创建默认配置文件"""
        try:
            default_config = self._load_default_config()
            self.config_dir.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, "w", encoding="utf-8") as f:
                toml.dump(default_config, f)
        except Exception as e:
            self.logger.error(f"创建默认配置文件失败: {e}")

    def _load_default_config(self) -> Dict[str, Any]:
        """加载默认配置"""
        try:
            return toml.load(self.default_config_file)
        except Exception as e:
            self.logger.error(f"加载默认配置失败: {e}")
            return {} 