# Configuration Files / 配置文件

This directory contains configuration files for the All The Skills import flow and runtime environment.

## Examples / 示例

The `examples/` directory contains sample configuration files:

- `skills-config.yaml` - YAML format configuration example
- `skills-config.json` - JSON format configuration example
- `ats.env.example` - generic environment configuration for the MCP server

## Usage / 使用方法

### Runtime environment for the MCP server / MCP 服务器运行环境

The ATS server reads runtime configuration from environment variables.

ATS 服务运行时从环境变量读取配置。

```bash
# Generic example
source config/examples/ats.env.example
all-the-skills
```

Supported runtime variables:

- `SKILL_CORTEX_ROOTS`: comma-separated skill roots scanned for `SKILL.md`
- `SKILL_CORTEX_CACHE_PATH`: cache file for the indexed snapshot
- `SKILL_CORTEX_TAGS_PATH`: tag registry file

### Import configuration / 导入配置

1. Copy an example file to your project root or desired location
2. Modify the repository list and settings as needed
3. Use with the import script:

```bash
# Use config file in current directory (auto-detected)
python import_skills.py --dry-run

# Use specific config file
python import_skills.py --config path/to/your-config.yaml
```

## Configuration Format / 配置格式

### Runtime env files / 运行时环境文件

ATS does not currently parse a dedicated runtime JSON or YAML file. Instead, use shell env files or configure the same variables in your MCP client.

ATS 当前不会解析专用的运行时 JSON 或 YAML 配置文件。请使用 shell 环境文件，或者在你的 MCP 客户端中注入同名环境变量。

### Repositories / 仓库配置

Each repository entry supports:
- `name`: Unique identifier for the repository
- `url`: Git repository URL
- `enabled`: Whether to include this repository (true/false)
- `branch`: Optional specific branch to use

### Settings / 设置

Future settings for advanced features:
- `incremental`: Enable incremental imports (planned feature)
- `validation`: Enable skill validation (planned feature)

## Auto-discovery / 自动发现

The import script automatically looks for these files in the current directory:
1. `skills-config.yaml`
2. `skills-config.yml` 
3. `skills-config.json`

If none are found, it uses the default repository list.
