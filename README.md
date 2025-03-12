# SQL执行器 (SQL Executor)

一个SQL查询工具，支持多种数据库类型，提供现代化的用户界面和便捷的查询管理功能。

## 功能特点

- 支持多种数据库
  - MySQL
  - PostgreSQL
  - Microsoft SQL Server
- 现代化的用户界面
  - SQL语法高亮
  - 查询结果表格显示
  - 可调整布局
  - 暗色/亮色主题
- 数据库连接管理
  - 分组管理
  - 快速搜索
  - 连接测试
- 查询功能
  - 多连接并行查询
  - 查询历史记录
  - 查询结果导出

## 系统要求

- Python 3.12 或更高版本
- 操作系统：Windows/Linux/macOS

## 安装说明

1. 克隆仓库：
```bash
git clone https://github.com/yourusername/sqlexec.git
cd sqlexec
```

2. 使用 uv 安装依赖：
```bash
uv sync
```

3. 运行应用程序：
```bash
uv run python -m sqlexec
```

## 配置说明

配置文件位于：`~/.sqlexec/config.toml`

示例配置：
```toml
[general]
theme = "light"  # 或 "dark"
language = "zh_CN"  # 或 "en_US"
show_system_tray = true
enable_notifications = true

[[connections]]
name = "本地MySQL"
alias = "local_mysql"
type = "mysql"
connection_string = "user:password@localhost:3306/dbname"
group = ["开发环境"]

[[connections]]
name = "生产PostgreSQL"
alias = "prod_pg"
type = "postgresql"
connection_string = "postgresql://user:password@host:5432/dbname"
group = ["生产环境"]
```

## 使用说明

1. 添加数据库连接
   - 点击"设置"按钮
   - 在"数据库"标签页中添加新连接
   - 填写连接信息并测试连接

2. 执行查询
   - 在左侧边栏选择要查询的数据库连接
   - 在查询编辑器中输入SQL语句
   - 点击"执行"按钮或按 Ctrl+Enter

3. 管理查询结果
   - 查看查询结果
   - 导出结果为CSV/Excel
   - 在标签页中切换不同的查询结果

## 日志位置

应用程序日志位于：`~/.sqlexec/logs/sqlexec.log`

## 常见问题

1. 连接失败
   - 检查连接字符串格式
   - 确认数据库服务器是否可访问
   - 验证用户名和密码

2. 界面显示问题
   - 检查是否安装了所有依赖
   - 尝试切换主题
   - 重启应用程序

## 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 许可证

本项目采用 MIT 许可证 