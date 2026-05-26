# OmicsFlow 开发文档

> **版本**: v0.2.0 | **更新**: 2026-05-26

---

## 目录

- [1. 项目概述](#1-项目概述)
- [2. 系统架构](#2-系统架构)
- [3. 目录结构](#3-目录结构)
- [4. 安装部署](#4-安装部署)
- [5. 后端开发指南](#5-后端开发指南)
- [6. 前端开发指南](#6-前端开发指南)
- [7. 分析管线](#7-分析管线)
- [8. 多智能体协同系统](#8-多智能体协同系统)
- [9. 公共数据与文献检索](#9-公共数据与文献检索)
- [10. 容器管理](#10-容器管理)
- [11. bioSkills 知识库](#11-bioskills-知识库)
- [12. API 接口文档](#12-api-接口文档)
- [13. 数据库设计](#13-数据库设计)
- [14. HPC 集群集成](#14-hpc-集群集成)
- [15. 生产部署](#15-生产部署)
- [16. 开发规范](#16-开发规范)
- [17. 路线图](#17-路线图)

---

## 1. 项目概述

### 1.1 定位

OmicsFlow 是基于 bioSkills 知识库的生物信息学分析平台，支持 Singularity 容器化和 Nextflow 工作流编排，适用于 HPC 高性能计算集群和本地开发环境。平台集成了 17 种分析管线、438 个 bioSkills 技能文档、6 个 AI 智能体协同、RBAC 权限管理、华大测序仪自动接入、公共数据检索和 Sugon HPC 集群适配。

### 1.2 核心功能

| 模块 | 说明 |
|------|------|
| 用户认证 | JWT 令牌认证，注册/登录，RBAC 四种角色 |
| 数据集管理 | 文件上传/下载，SHA256 校验，元数据管理 |
| 分析管线 | 17 种 Nextflow 工作流，覆盖主流组学分析 |
| 任务调度 | 异步队列执行，WebSocket 实时状态推送，自动报告生成 |
| 测序仪集成 | 华大 G99/T1+/T7 自动数据扫描接入 |
| bioSkills 知识库 | 438 个生信技能文档，AI 意图识别 |
| AI 助手 | 对话式分析推荐，自然语言→管线参数 |
| 多智能体系统 | 6 个 AI 智能体事件驱动协同工作 |
| 公共数据检索 | GEO/SRA 数据搜索下载 + PubMed 文献检索 |
| 结果管理 | 打包下载、分享链接、Plotly 交互可视化 |
| 通知系统 | 企业微信 Webhook + 邮件 SMTP |
| HPC 集成 | Sugon 集群 PBS/Torque 作业提交 |

### 1.3 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | React 18 + TypeScript + Vite 5 + Tailwind CSS 3 + React Query 5 |
| 后端 | FastAPI 0.109+ + SQLAlchemy 2.0 (async) + Pydantic v2 |
| 数据库 | PostgreSQL 15 + Redis 7 |
| 工作流 | Nextflow DSL2 (14 个工作流, 22 个模块, 60+ 进程) |
| 容器 | Singularity 3.8+ / Docker |
| AI | OpenAI GPT-4 / Anthropic Claude (可选, 含规则引擎降级) |
| 智能体 | 6 Agent 协同 (数据管家/方案顾问/参数优化师/结果解读员/质控哨兵/文献助手) |
| HPC | PBS/Torque (Sugon NIDVD 集群) |
| CI/CD | GitHub Actions |

---

## 2. 系统架构

### 2.1 六层架构

```
┌─────────────────────────────────────────────────┐
│  用户交互层 (React 18 + TypeScript + Tailwind)   │
│  Dashboard/AI助手/公共数据/测序仪/管线/任务/用户  │
├─────────────────────────────────────────────────┤
│  后端服务层 (FastAPI + SQLAlchemy)               │
│  REST API / WebSocket / RBAC / 通知 / 可视化     │
├─────────────────────────────────────────────────┤
│  多智能体层 (6 Agent + Orchestrator)             │
│  数据管家/方案顾问/参数优化/结果解读/QC哨兵/文献  │
├─────────────────────────────────────────────────┤
│  工作流编排层 (Nextflow DSL2 + Singularity)      │
│  17 种管线 / 22 个模块 / 60+ 进程                 │
├─────────────────────────────────────────────────┤
│  AI 知识注入层 (bioSkills + LLM)                 │
│  438 个技能 / 意图识别 / 对话式分析               │
├─────────────────────────────────────────────────┤
│  数据存储层 (PostgreSQL + 本地文件 + PBS/Torque)  │
└─────────────────────────────────────────────────┘
```

### 2.2 请求流程

```
浏览器 → React (Vite/Nginx) → /api/v1/* → FastAPI
    → JWT 认证 → RBAC 权限 → 业务逻辑
        → PostgreSQL (元数据)
        → Celery + Redis (异步任务)
            → Nextflow (工作流执行)
                → Singularity (容器化分析)
            → WebSocket (实时推送)
        → 本地存储 (文件/结果)
        → 通知系统 (微信/邮件)
```

### 2.3 智能体协同流程

```
测序仪下机数据
    ↓
🔬 数据管家: 检测数据类型(WGS/RNA-seq/16S) + QC 评估
    ↓
📋 方案顾问: 推荐管线 + 📚 文献助手检索参考文献
    ↓
⚙️ 参数优化师: 自动配置最优参数 (线程数/内存/阈值)
    ↓
   Celery 任务执行
    ↓
🚨 质控哨兵: 实时监控 (QC 阈值/进度/错误)
    ↓
📊 结果解读员: 自动生成报告 + AI 解读关键发现
```

---

## 3. 目录结构

```
OmicsFlow/
├── backend/                           # FastAPI 后端
│   ├── api/                           # API 路由层 (10 个模块)
│   │   ├── __init__.py                #   路由汇总注册
│   │   ├── main.py                    #   应用入口
│   │   ├── auth.py                    #   认证接口
│   │   ├── datasets.py                #   数据集接口
│   │   ├── pipelines.py               #   管线接口
│   │   ├── tasks.py                   #   任务接口 (异步/WebSocket)
│   │   ├── skills.py                  #   技能库接口
│   │   ├── ai.py                      #   AI 接口 (意图/对话)
│   │   ├── sequencers.py              #   测序仪接口
│   │   ├── projects.py                #   项目接口
│   │   ├── results.py                 #   结果接口 (下载/可视化)
│   │   └── public_data.py             #   公共数据接口 (GEO/SRA/PubMed)
│   ├── models/
│   │   ├── database.py                # ORM 模型
│   │   └── schemas.py                 # Pydantic Schema
│   ├── services/                      # 业务逻辑层
│   │   ├── task_queue.py              #   异步任务队列
│   │   ├── websocket.py               #   WebSocket 管理
│   │   ├── hpc_scheduler.py           #   PBS/Torque 集成
│   │   ├── report_generator.py        #   自动报告
│   │   ├── visualization.py           #   Plotly 可视化
│   │   ├── download_service.py        #   打包/分享
│   │   ├── notification.py            #   通知服务
│   │   ├── ai_chat.py                 #   AI 对话服务
│   │   ├── public_data.py             #   公共数据下载
│   │   ├── rbac.py                    #   RBAC 权限
│   │   └── agents/                    #   多智能体系统
│   │       ├── __init__.py
│   │       ├── data_steward.py        #     🔬 数据管家
│   │       ├── pipeline_advisor.py    #     📋 方案顾问
│   │       ├── param_optimizer.py     #     ⚙️ 参数优化师
│   │       ├── results_interpreter.py #     📊 结果解读员
│   │       ├── qc_sentinel.py         #     🚨 质控哨兵
│   │       ├── literature_agent.py    #     📚 文献助手
│   │       └── orchestrator.py        #     🎯 编排器
│   ├── middleware.py                  # 中间件 (追踪/限流/安全头)
│   └── config.py                      # 配置管理
│
├── frontend/                          # React 前端
│   └── src/
│       ├── App.tsx                    # 路由 (10 个页面)
│       ├── api/client.ts              # Axios 客户端 (9 个 API 模块)
│       ├── components/Layout.tsx      # 侧边栏导航 (9 个菜单项)
│       ├── pages/
│       │   ├── DashboardPage.tsx
│       │   ├── LoginPage.tsx
│       │   ├── AIChatPage.tsx         # AI 对话助手
│       │   ├── DataBrowserPage.tsx    # 公共数据/文献检索
│       │   ├── ResultsPage.tsx        # 结果查看 (火山图/热图/CNV)
│       │   ├── SequencersPage.tsx
│       │   ├── PipelinesPage.tsx      # 17 种管线选择器
│       │   ├── TasksPage.tsx
│       │   ├── DatasetsPage.tsx
│       │   └── UsersPage.tsx
│       └── i18n/                      # en.json / zh.json
│
├── workflows/                         # 14 个 Nextflow 工作流
│   ├── main.nf                        # 主路由 (17 种管线)
│   ├── rnaseq_workflow.nf
│   ├── wgs_variant_workflow.nf
│   ├── de_workflow.nf
│   ├── cnv_workflow.nf
│   ├── metagenomics_workflow.nf
│   ├── amplicon_workflow.nf           # DADA2 + Phyloseq
│   ├── tcr_workflow.nf                # MiXCR
│   ├── atac_workflow.nf               # MACS3 + chromVAR
│   ├── spatial_workflow.nf            # Squidpy
│   ├── chipseq_workflow.nf            # MACS3 + HOMER
│   ├── smrna_workflow.nf              # miRDeep2 / miRge3
│   ├── somatic_workflow.nf            # Mutect2
│   ├── methylation_workflow.nf        # Bismark + methylKit
│   ├── longread_workflow.nf           # Minimap2 + Sniffles
│   ├── wes_workflow.nf                # BWA + GATK + Panel
│   └── proteomics_workflow.nf         # MaxQuant / DIA-NN
│
├── modules/                           # 22 个 Nextflow 模块目录
├── skills/                            # 438 个 bioSkills
├── containers/                        # 4 个 Singularity 定义
├── configs/nextflow.sugon.config      # Sugon HPC 配置
├── database/schema.sql                # PostgreSQL 建表
├── docker/                            # Docker Compose
├── scripts/                           # 部署脚本
└── .github/workflows/ci.yml           # CI/CD
```

---

## 4. 安装部署

### 4.1 环境变量 (.env)

```bash
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/pipeline_test
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-secret-key
DEBUG=true
NEXTFLOW_PATH=/usr/local/bin/nextflow
WORKFLOW_DIR=.../workflows
OUTPUT_DIR=/data/output
OPENAI_API_KEY=           # 可选
ANTHROPIC_API_KEY=        # 可选
WECHAT_WEBHOOK=           # 企业微信 (可选)
SMTP_HOST=                # 邮件通知 (可选)
```

### 4.2 本地开发

```bash
# 后端
cd backend && pip install -e . && uvicorn api.main:app --port 8000

# Celery Worker
celery -A services.celery_app worker -Q omicsflow_default,omicsflow_pipelines -l info

# 前端
cd frontend && npm install && npm run dev
```

### 4.3 Docker / HPC

```bash
cd docker && ./deploy.sh                              # Docker
cd scripts && ./build_containers.sh && ./deploy.sh    # HPC
```

---

## 5. 后端开发指南

### 5.1 服务层一览 (16+ 个服务)

| 服务 | 文件 | 功能 |
|------|------|------|
| database | `services/database.py` | 异步引擎/会话 |
| auth | `services/auth.py` | bcrypt + JWT |
| task_queue | `services/task_queue.py` | 异步任务队列 (本地/PBS) |
| celery_app | `services/celery_app.py` | Celery + Redis 分布式队列 |
| celery_tasks | `services/celery_tasks.py` | Celery 任务定义 (pipeline/GPU/cleanup) |
| websocket | `services/websocket.py` | WebSocket 连接管理 |
| hpc_scheduler | `services/hpc_scheduler.py` | PBS/Torque 集成 |
| report_generator | `services/report_generator.py` | 自动报告 |
| visualization | `services/visualization.py` | Plotly 可视化 (火山图/热图/PCA) |
| download_service | `services/download_service.py` | 打包/分享 |
| notification | `services/notification.py` | 企业微信/邮件 |
| ai_chat | `services/ai_chat.py` | AI 对话服务 (规则+LLM) |
| public_data | `services/public_data.py` | GEO/SRA/PubMed |
| data_scanner | `services/data_scanner.py` | 测序仪数据扫描 (5种布局) |
| rbac | `services/rbac.py` | RBAC 权限 (4角色+资源级) |
| agents/orchestrator | `services/agents/orchestrator.py` | 多智能体编排 (6 Agent) |

### 5.2 RBAC 权限

| 角色 | 权限 |
|------|------|
| admin | 全部 |
| bioinformatician | 运行管线/任务、管理数据集 |
| librarian | 创建项目、管理样本 |
| viewer | 只读 |

### 5.3 中间件

- **RequestTracingMiddleware**: X-Request-ID
- **RateLimitMiddleware**: 120 RPM
- **SecurityHeadersMiddleware**: XSS/Content-Type 等

---

## 6. 前端开发指南

### 6.1 路由 (10 个页面)

| 路径 | 组件 | 说明 |
|------|------|------|
| `/` | DashboardPage | 仪表盘 |
| `/login` | LoginPage | 登录 |
| `/ai-chat` | AIChatPage | AI 对话助手 |
| `/data-browser` | DataBrowserPage | 公共数据/文献 |
| `/sequencers` | SequencersPage | 测序仪管理 |
| `/pipelines` | PipelinesPage | 管线 (17 种) |
| `/tasks` | TasksPage | 任务管理 |
| `/results` | ResultsPage | 结果查看 (火山图/热图/CNV) |
| `/datasets` | DatasetsPage | 数据集 |
| `/users` | UsersPage | 用户管理 |

---

## 7. 分析管线

### 7.1 17 种管线

| # | 管线 | 技术栈 |
|---|------|--------|
| 1 | RNA-seq | STAR + Salmon |
| 2 | WGS 变异 | BWA-MEM2 + GATK |
| 3 | 差异表达 | edgeR / DESeq2 |
| 4 | CNV | CNVkit |
| 5 | 宏基因组 | Kraken2 + Bracken |
| 6 | 16S/ITS | DADA2 + Phyloseq |
| 7 | TCR/BCR | MiXCR |
| 8 | ATAC-seq | Bowtie2 + MACS3 |
| 9 | 空间转录组 | Squidpy |
| 10 | ChIP-seq | Bowtie2 + MACS3 + HOMER |
| 11 | small RNA | miRDeep2 / miRge3 |
| 12 | 体细胞变异 | GATK Mutect2 |
| 13 | 甲基化 | Bismark + methylKit |
| 14 | 长读长 | Minimap2 + Sniffles + Clair3 |
| 15 | WES | BWA + GATK + Panel QC |
| 16 | 蛋白质组 | MaxQuant / DIA-NN |
| 17 | 质控 | FastQC + MultiQC |

### 7.2 22 个模块目录

含 60+ 个 Nextflow 进程，覆盖 STAR/BWA/Bowtie2/Minimap2/GATK/Mutect2/Clair3/Salmon/DADA2/MiXCR/MACS3/Kraken2/Scanpy/Squidpy/Bismark/MaxQuant/DIA-NN/miRDeep2 等工具。

---

## 8. 多智能体协同系统

### 8.1 架构

6 个专用智能体 + 1 个编排器，事件驱动协同：

```
services/agents/
├── __init__.py
├── data_steward.py          # 🔬 数据管家
├── pipeline_advisor.py      # 📋 方案顾问
├── param_optimizer.py       # ⚙️ 参数优化师
├── results_interpreter.py   # 📊 结果解读员
├── qc_sentinel.py           # 🚨 质控哨兵
├── literature_agent.py      # 📚 文献助手
└── orchestrator.py          # 🎯 编排器
```

### 8.2 各智能体职责

| 智能体 | 输入 | 输出 | 触发时机 |
|--------|------|------|---------|
| 🔬 数据管家 | FASTQ 文件列表 | 数据类型/样本数/PE/推荐 | 新数据到达 |
| 📋 方案顾问 | 数据类型 + 物种 | 管线/工具/输入输出/运行时间 | 创建任务 |
| ⚙️ 参数优化师 | 管线类型 + 数据量 | 线程/内存/时限 | 任务启动 |
| 📊 结果解读员 | 输出目录 | key_findings/QC状态/建议 | 任务完成 |
| 🚨 质控哨兵 | 比对率/重复率 | pass/warn/fail | 运行中 |
| 📚 文献助手 | 分析类型 | 关键论文/bioSkills | 方案推荐 |

### 8.3 编排器事件

```python
from services.agents.orchestrator import orchestrator

# 事件1: 新数据到达
result = await orchestrator.on_new_data(fastq_files, metadata)

# 事件2: 任务启动
result = await orchestrator.on_task_start("rnaseq", {"sample_count": 6, "total_size_gb": 50})

# 事件3: 任务完成
result = await orchestrator.on_task_complete(task_id, "rnaseq", "/data/output/task123")

# 全流程规划
plan = await orchestrator.full_analysis_plan("rnaseq", "Homo sapiens", "差异表达")
```

### 8.4 开发新智能体

1. 在 `services/agents/` 创建 `{agent_name}.py`
2. 实现 `async def analyze/process/check` 方法
3. 在 `orchestrator.py` 中注册并关联事件

---

## 9. 公共数据与文献检索

### 9.1 服务 (`services/public_data.py`)

| 方法 | 数据源 | 功能 |
|------|--------|------|
| `search_geo()` | GEO (NCBI E-utilities) | 搜索数据集 |
| `search_sra()` | SRA | 搜索测序 Run |
| `download_sra_run()` | SRA Toolkit | prefetch + fasterq-dump |
| `search_pubmed()` | PubMed | 文献检索 |
| `suggest_analysis_plan()` | PubMed + 知识库 | 方案推荐 |

### 9.2 API (`api/public_data.py`)

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/data/geo/search` | 搜索 GEO |
| POST | `/data/sra/search` | 搜索 SRA |
| POST | `/data/sra/download` | 下载 SRA Run |
| POST | `/data/pubmed/search` | 搜索 PubMed |
| POST | `/data/literature/plan` | 文献驱动方案推荐 |
| POST | `/results/download/package` | 打包下载 |
| POST | `/results/download/share` | 创建分享链接 |
| GET | `/results/download/share/{token}` | 下载共享文件 |
| POST | `/results/visualize/volcano` | 生成火山图 |
| POST | `/results/visualize/heatmap` | 生成热图 |

### 9.3 前端 (`DataBrowserPage.tsx`)

4 个标签页: GEO 数据集 / SRA 测序数据 / PubMed 文献 / 分析方案推荐

---

## 10. 容器管理

| 容器 | 内容 |
|------|------|
| omicsflow.sif | Python 3.10 + Nextflow + FastAPI |
| bioconductor.sif | R 4.3.1 + edgeR + DESeq2 |
| cnvkit.sif | CNVkit |
| qc_tools.sif | FastQC + MultiQC |

---

## 11. bioSkills 知识库

438 个技能文档，覆盖 40+ 生信分析大类。`scripts/sync_bioskills.py` 从 GPTomics/bioSkills 仓库同步。

---

## 12. API 接口文档

基础路径: `/api/v1`

| 模块 | 端点示例 | 说明 |
|------|---------|------|
| 认证 | POST /auth/login, /auth/register | 登录/注册 |
| 任务 | POST /tasks/{id}/run, WS /tasks/ws/{id} | 执行/WebSocket |
| AI | POST /ai/chat, /ai/intent | 对话/意图 |
| 公共数据 | POST /data/geo/search, /data/pubmed/search | GEO/PubMed |
| 结果 | POST /results/download/package, /results/visualize/volcano | 下载/可视化 |
| 测序仪 | POST /sequencers/{id}/scan | 扫描 |
| 健康 | GET /health | uptime/tasks/WS |

Swagger UI: `http://localhost:8000/docs`

---

## 13. 数据库设计

| 表 | 说明 |
|----|------|
| users | 用户 (roles JSONB) |
| datasets | 数据集 |
| pipelines | 管线 |
| tasks | 任务 (input_params JSONB) |
| task_results | 结果 |
| skills | 技能 |
| sequencers | 测序仪 |
| sequencer_runs | 运行 |
| samples | 样本 |
| projects | 项目 |

---

## 14. HPC 集群集成

### Sugon 集群

| 节点 | CPU | GPU |
|------|-----|-----|
| computer1~4 | AMD EPYC 7763 (64C) 1TB | - |
| gpu1~9 | Xeon Gold 6326 (16C) 512G | 4×A40 48G |
| gpu10~17 | Xeon Gold 5317 (12C) 256G | 4/8×RTX3090 |
| gpu18 | Xeon Gold 5317 (12C) 256G | 2×Z100L |

PBS/Torque 集成: `services/hpc_scheduler.py`

---

## 15. 生产部署

- 中间件: 安全头 → 限流 → 请求追踪
- 日志: JSON 结构化 (LOG_JSON=true)
- Docker: 2 workers + HEALTHCHECK
- CI/CD: GitHub Actions (test → build → lint)

---

## 16. 开发规范

- 后端: Black + Ruff + Python 3.10+ 类型注解
- 前端: 函数组件 + Hooks + React Query + Tailwind
- 安全: bcrypt + RBAC + CORS + SECRET_KEY

---

## 17. 路线图

### 已实现 (v0.2.0)

- [x] 17 种分析管线 (22 模块, 60+ 进程)
- [x] 438 个 bioSkills
- [x] 6 个 AI 智能体协同
- [x] RBAC 四角色权限
- [x] 华大测序仪集成 (G99/T1+/T7)
- [x] 异步任务队列 + WebSocket
- [x] AI 对话式分析助手
- [x] 公共数据检索 (GEO/SRA/PubMed)
- [x] 自动分析报告
- [x] 打包下载 + 分享链接
- [x] Plotly 交互可视化
- [x] 企业微信 + 邮件通知
- [x] Sugon HPC PBS 集成
- [x] 结构化日志 + 中间件
- [x] Docker + CI/CD
- [x] 中英文国际化
- [x] CORS 生产限制 + 密钥检查
- [x] PID 文件管理 (替代 pkill)
- [x] 数据库 UUID + 性能索引 (migration_v020.sql)

### 🔵 规划中

- [ ] WebSocket 前端实时日志流 Hook
- [ ] 单元测试 (pytest)
- [ ] Alembic ORM 迁移工具
- [ ] IGV.js 基因组浏览器
- [ ] Grafana + Prometheus 监控
- [ ] S3 兼容对象存储
- [ ] Pipeline Builder 拖拽编辑器
