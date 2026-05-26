# OmicsFlow - 生物信息学分析平台

> 基于 bioSkills 知识库的一站式组学分析平台，支持 Singularity 容器化、Nextflow 工作流编排、Celery 分布式任务队列、HPC 集群提交、多智能体协同和 AI 辅助分析。

## 🧬 项目概述

OmicsFlow 为生物信息学实验室提供从测序仪下机数据到分析报告的完整解决方案：

- **17 种分析管线** 覆盖主流组学分析场景 ✅ 已实现
- **438 个 bioSkills** 知识技能文档 ✅ 已实现
- **6 个 AI 智能体** 事件驱动协同工作 ✅ 已实现
- **RBAC 权限管理** — 管理员/生信人员/建库人员/查看者 ✅ 已实现
- **华大测序仪集成** — G99、T1+、T7、i100、GridION 自动数据接入 ✅ 已实现
- **AI 智能助手** — 自然语言推荐最佳分析管线 ✅ 已实现
- **公共数据检索** — GEO/SRA 数据搜索下载 + PubMed 文献检索 ✅ 已实现
- **Plotly 交互可视化** — 火山图/热图/PCA/CNV 图谱 ✅ 已实现
- **Celery + Redis 分布式任务队列** ✅ 已实现
- **Sugon HPC 集群适配** — PBS/Torque 作业提交 ✅ 已实现
- **数据库优化** — UUID 主键 + 性能索引 ✅ 已实现 (migration_v020.sql)
- **生产安全** — CORS 限制 + 密钥检查 + PID 文件管理 ✅ 已实现

## 📊 分析管线

| 管线 | 技术栈 | 用途 |
|------|--------|------|
| RNA-seq | STAR + Salmon | 基因表达定量 |
| WGS 变异 | BWA-MEM2 + GATK | 体细胞/胚系变异检测 |
| 差异表达 | edgeR / DESeq2 | 条件间基因差异分析 |
| CNV | CNVkit | 拷贝数变异检测 |
| 宏基因组 | Kraken2 + Bracken | 物种分类与丰度 |
| 16S/ITS | DADA2 + Phyloseq | 扩增子微生物组 |
| TCR/BCR | MiXCR | 免疫组库分析 |
| ATAC-seq | Bowtie2 + MACS3 | 染色质可及性 |
| 空间转录组 | Squidpy | 空间基因表达 |
| ChIP-seq | Bowtie2 + MACS3 + HOMER | 转录因子/组蛋白修饰 |
| small RNA | miRDeep2 / miRge3 | miRNA 发现与定量 |
| 体细胞变异 | GATK Mutect2 | 肿瘤-正常配对变异 |
| 甲基化 | Bismark + methylKit | WGBS/RRBS 甲基化 |
| 长读长 | Minimap2 + Sniffles + Clair3 | ONT/PacBio 测序 |
| WES | BWA + GATK + Panel QC | 外显子靶向测序 |
| 蛋白质组 | MaxQuant / DIA-NN | DDA/DIA 质谱分析 |
| 质控 | FastQC + MultiQC | 测序数据质量评估 |

## 🤖 多智能体协同系统

OmicsFlow 内置 6 个专用智能体，事件驱动自动协同：

| 智能体 | 职责 | 触发时机 |
|--------|------|---------|
| 🔬 **数据管家** | 检测数据类型 + QC 评估 | 新数据到达 |
| 📋 **方案顾问** | 推荐分析管线 + 工具 | 用户创建任务 |
| ⚙️ **参数优化师** | 自动调优线程/内存/时限 | 管线启动前 |
| 📊 **结果解读员** | 解读 QC 指标 + 关键发现 | 任务完成后 |
| 🚨 **质控哨兵** | 运行中监控阈值异常 | 任务运行中 |
| 📚 **文献助手** | 关键论文引用 + bioSkills 关联 | 方案推荐时 |

```
新数据 → 🔬数据管家(识别) → 📋方案顾问(推荐) → 📚文献助手(引用)
任务完成 → 📊结果解读员(解读) + 🚨质控哨兵(QC检查)
```

## 🔍 公共数据与文献

| 功能 | 数据源 | 说明 |
|------|--------|------|
| 数据集搜索 | GEO (NCBI) | 搜索 GSE 数据集，返回样本数/物种/平台 |
| 测序数据搜索 | SRA (NCBI) | 搜索 Run ID，支持 prefetch 下载 |
| 文献检索 | PubMed | 关键词搜索，含期刊/作者/DOI |
| 分析方案推荐 | PubMed + 知识库 | 选择物种+数据类型→推荐管线+参考文献 |

## 🏗️ 技术架构

```
┌─────────────────────────────────────────────────┐
│  用户交互层: React 18 + TypeScript + Tailwind    │
│  - Dashboard / AI 助手 / 公共数据 / 结果查看     │
├─────────────────────────────────────────────────┤
│  后端服务: FastAPI + SQLAlchemy (async)          │
│  - REST API / WebSocket / RBAC / 通知            │
├─────────────────────────────────────────────────┤
│  多智能体层: 6 个 AI Agent + Orchestrator         │
│  - 数据管家 / 方案顾问 / 参数优化师              │
│  - 结果解读员 / 质控哨兵 / 文献助手              │
├─────────────────────────────────────────────────┤
│  任务队列: Celery + Redis                        │
│  - 分布式执行 / GPU 队列 / 定时任务              │
├─────────────────────────────────────────────────┤
│  工作流编排: Nextflow DSL2 + Singularity         │
│  - 17 种管线 / 22 个模块 / 60+ 进程              │
├─────────────────────────────────────────────────┤
│  AI 知识注入: bioSkills + LLM                    │
│  - 438 个技能 / 意图识别 / 对话式分析             │
├─────────────────────────────────────────────────┤
│  数据存储: PostgreSQL + 本地文件 + PBS/Torque     │
└─────────────────────────────────────────────────┘
```

## 🚀 快速开始

### 环境要求

| 依赖 | 版本 |
|------|------|
| Python | >= 3.10 |
| Node.js | >= 18 |
| PostgreSQL | >= 15 |
| Redis | >= 7 |
| Nextflow | >= 23.04 |
| Singularity | >= 3.8 |

### 安装部署

```bash
# 1. 配置环境变量
cp .env.example .env

# 2. 初始化数据库 + 运行迁移
cd database && ./init.sh
psql -h localhost -U postgres -d pipeline_test -f migration_v020.sql

# 3. 启动后端
cd backend && pip install -e . && uvicorn api.main:app --port 8000

# 4. 启动 Celery Worker
celery -A services.celery_app worker -Q omicsflow_default,omicsflow_pipelines -l info

# 5. 启动前端
cd frontend && npm install && npm run dev
```

### Docker 部署

```bash
cd docker && ./deploy.sh
```

## 📁 目录结构

```
OmicsFlow/
├── backend/                # FastAPI 后端
│   ├── api/                # REST API (12 个模块)
│   ├── models/             # ORM + Schema
│   ├── services/           # 业务逻辑 (16+ 服务)
│   │   ├── celery_app.py   #   Celery + Redis
│   │   ├── celery_tasks.py #   分布式任务
│   │   ├── data_scanner.py #   测序仪数据扫描
│   │   ├── visualization.py#   Plotly 可视化
│   │   ├── notification.py #   企业微信/邮件
│   │   ├── ai_chat.py      #   AI 对话
│   │   ├── public_data.py  #   GEO/SRA/PubMed
│   │   └── agents/         #   6 个 AI 智能体 + 编排器
│   ├── middleware.py        # 请求追踪/限流/安全头
│   └── config.py           # 配置管理
├── frontend/               # React + TypeScript
│   └── src/pages/          # 10 个页面
├── workflows/              # 17 个 Nextflow 工作流
├── modules/                # 22 个模块目录 (60+ 进程)
├── skills/                 # 438 个 bioSkills
├── containers/             # Singularity 定义
├── configs/                # nextflow.sugon.config
├── database/               # schema.sql + migration_v020.sql
├── docker/                 # Docker Compose
└── .github/workflows/      # CI/CD
```

## 🔐 角色权限

| 角色 | 说明 | 权限范围 |
|------|------|---------|
| `admin` | 管理员 | 用户管理、测序仪管理、全部 CRUD |
| `bioinformatician` | 生信分析人员 | 运行管线/任务、管理数据集 |
| `librarian` | 建库人员 | 创建项目、管理样本/数据集 |
| `viewer` | 查看者 | 只读访问 |

## 🖥️ 功能模块

### 测序仪集成
- 支持华大 G99/T1+/T7 及 Nanopore i100/GridION
- 5 种测序仪目录布局自动识别
- 自动扫描数据目录，检测新 Run

### 任务队列
- Celery + Redis 分布式队列
- 独立 GPU 队列 (A40/RTX3090/Z100L)
- WebSocket 实时推送任务状态和日志
- 支持本地执行和 PBS/Torque 集群提交

### 结果查看
- Plotly 交互式可视化 (火山图/热图/PCA/CNV)
- 打包下载 (tar.gz/zip) + 限时分享链接
- 自动 Markdown 分析报告

### AI 助手
- 自然语言 → 推荐最佳管线
- 17 种管线中英文意图识别
- 会话上下文管理 (20 轮对话)

### 通知系统
- 企业微信 Webhook + 邮件 SMTP

## 📖 API 文档

Swagger UI: `http://localhost:8000/docs`
健康检查: `http://localhost:8000/health`

## ✅ 实现状态

### 已实现
- [x] 17 种分析管线 (22 模块, 60+ 进程)
- [x] 438 个 bioSkills (118K+ 行内容)
- [x] 6 个 AI 智能体协同
- [x] RBAC 四角色权限 + 资源级访问控制
- [x] 华大测序仪集成 (G99/T1+/T7/i100/GridION)
- [x] Celery + Redis 分布式任务队列
- [x] WebSocket 实时推送
- [x] AI 对话式分析助手
- [x] 公共数据检索 (GEO/SRA/PubMed)
- [x] 自动分析报告
- [x] 打包下载 + 分享链接
- [x] Plotly 交互可视化 (火山图/热图/PCA/CNV)
- [x] 企业微信 + 邮件通知
- [x] Sugon HPC PBS 集成
- [x] 结构化日志 + 中间件
- [x] CORS 限制 + 密钥检查
- [x] PID 文件管理 (替代 pkill)
- [x] 数据库 UUID + 性能索引 (migration_v020.sql)
- [x] Docker + CI/CD
- [x] 中英文国际化

### 🔵 规划中
- [ ] WebSocket 前端实时日志流 Hook
- [ ] 单元测试 (pytest)
- [ ] Alembic ORM 迁移工具
- [ ] IGV.js 基因组浏览器
- [ ] Grafana + Prometheus 监控
- [ ] S3 兼容对象存储
- [ ] Pipeline Builder 拖拽编辑器

## 📜 许可证

MIT License