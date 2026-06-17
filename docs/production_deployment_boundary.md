# 生产部署文件边界 v2026-06-17

## 审计结论

- **docs/ 是否被运行时引用**：❌ 否。`backend/` 中零处引用 `docs/` 路径。
- **CURRENT_HANDOFF / 方案文档是否被引用**：❌ 否。均为人类可读文档，不参与程序执行。
- **backend/knowledge 是否必须**：✅ 是。`backend/knowledge/business_models/*.yaml` + `location_profiles.yaml` + `sources/source_manifest.yaml` 被 `business_model_service.py` 和 `location_profile_service.py` 在运行时动态加载，用于报告生成。

## 生产必须保留

### backend/（核心）

```
backend/
  main.py                        # 启动入口
  config.py                      # 配置
  database.py                    # 数据库
  auth.py                        # 认证
  requirements.txt               # 依赖
  services/                      # 全部 service 模块
    *.py
  knowledge/                     # ⚠️ 运行时必需
    location_profiles.yaml
    location_profile_schema.yaml
    business_model_schema.yaml
    source_card_schema.yaml
    business_models/             # 12 个 YAML
      *.yaml
    sources/
      source_manifest.yaml
      *.yaml                     # 15 个已吸收 + 3 个 candidate
  prompts/                       # LLM prompt 配置
    *.py
  models/                        # ORM 模型
    *.py
  routers/                       # API 路由
    *.py
  admin/                         # 管理后台
    *.html
  ai_providers/                  # AI 提供商适配
    *.py
  location_tool.db               # SQLite 数据库（如存在）
```

### uniapp/ 或 miniprogram/

```
uniapp/
  src/                           # 小程序源码
  package.json
  vite.config.*
```

编译产物 `dist/build/mp-weixin` 部署到微信开发者工具。

## 生产必须排除

| 目录/文件 | 原因 |
|-----------|------|
| `docs/` | 纯文档，运行时零引用，不参与程序执行 |
| `.claude/` | Claude Code 内部工作区 |
| `.git/` | Git 仓库 |
| `.vscode/` `.idea/` | IDE 配置 |
| `.env` | 密钥文件（不应入仓库） |
| `logo-1/` | 未跟踪资源 |
| `Desktop/` 级别的交接文件 | 非项目文件 |
| `backend/logs/` | 运行时日志 |
| `backend/c4_test.json` | 测试用配置 |
| `backend/__pycache__/` `*.pyc` | 编译缓存 |
| `miniprogram/` 与 `uniapp/` 中选择一个部署 | 二者有重叠，通常只部署 uniapp 编译产物 |

## backend/knowledge 边界

- **YAML 文件**：运行时被 `business_model_service.load_business_model()` 动态加载，必须保留。
- **source card 文件**：被 `check_knowledge_schema_rules.py` 测试引用，但**不参与报告生成运行时**。从纯运行角度看可排除，但保留可让服务器端跑 schema 测试验证一致性。建议保留。
- **candidate_*.yaml**：candidate_only 来源卡，不影响报告行为，可排除。建议保留以便服务器端 T17/T18 测试验证。

## 当前 .gitignore 覆盖

```gitignore
.claude/
.env
backend/.env
backend/c4_test.json
zhidexuan/       # 旧备份
backend/logs/
logo-1/
```

**未覆盖项**：`docs/` 不在 .gitignore 中（有意提交到仓库），但也不应部署到生产。

## 部署建议

生产路径：`/www/wwwroot/location-tool/`

最小部署步骤：

```bash
# 同步 backend（排除 docs/logs/__pycache__）
rsync -av --exclude 'docs/' --exclude 'backend/logs/' --exclude '__pycache__/' \
  /path/to/local/location-tool/backend/ /www/wwwroot/location-tool/backend/

# 编译小程序
cd /path/to/local/location-tool/uniapp && npm run build:mp-weixin

# 重启后端
pkill -f "python main.py" || true
cd /www/wwwroot/location-tool/backend && nohup python main.py > app.log 2>&1 &
```

## 禁止进入生产

- ❌ 任何 `docs/` 下的文件（包括 audit/checklist/plan/matrix）
- ❌ `CURRENT_HANDOFF`、交接文档
- ❌ 原始资料文件（PDF/电子书/下载文件）
- ❌ `.env` 或任何含密钥文件
- ❌ 测试临时文件、debug 输出
