"""
Automatic analysis report generator.
Generates Markdown/QC reports after pipeline completion.
"""
import os
import csv
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List

logger = logging.getLogger("omicsflow.report")


class ReportGenerator:
    """Generates analysis reports from pipeline output."""

    def generate_report(self, task_id: str, pipeline_type: str, output_dir: str) -> Optional[str]:
        """Generate a Markdown report for completed analysis."""
        output_path = Path(output_dir)
        if not output_path.exists():
            return None

        generators = {
            "rnaseq": self._rnaseq_report,
            "wgs": self._wgs_report,
            "de": self._de_report,
            "cnv": self._cnv_report,
            "metagenomics": self._metagenomics_report,
            "qc": self._qc_report,
        }

        gen = generators.get(pipeline_type, self._generic_report)
        report = gen(task_id, output_path)
        
        report_path = output_path / "analysis_report.md"
        report_path.write_text(report, encoding="utf-8")
        logger.info(f"Report generated: {report_path}")
        return str(report_path)

    def _rnaseq_report(self, task_id: str, output_dir: Path) -> str:
        lines = [
            f"# RNA-seq 分析报告",
            f"",
            f"**任务ID**: `{task_id}`",
            f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"",
            f"## 1. 分析概要",
            f"",
            f"| 指标 | 值 |",
            f"|------|-----|",
        ]

        # Check for STAR output
        star_logs = list(output_dir.rglob("*.Log.final.out"))
        if star_logs:
            for log in star_logs[:3]:
                content = log.read_text(errors="ignore")
                for line in content.split("\n"):
                    if "Number of input reads" in line:
                        reads = line.split("|")[-1].strip()
                        lines.append(f"| 总输入 Reads | {reads} |")
                    elif "Uniquely mapped reads number" in line:
                        mapped = line.split("|")[-1].strip()
                        lines.append(f"| 唯一比对 Reads | {mapped} |")
                    elif "Uniquely mapped reads %" in line:
                        pct = line.split("|")[-1].strip()
                        lines.append(f"| 唯一比对率 | {pct} |")

        # Check for Salmon quant
        salmon_counts = list(output_dir.rglob("*.merged.gene_counts.tsv"))
        if salmon_counts:
            lines.append(f"")
            lines.append(f"## 2. 定量结果")
            lines.append(f"")
            lines.append(f"基因计数矩阵: `{salmon_counts[0].name}`")
            
            with open(salmon_counts[0]) as f:
                reader = csv.reader(f, delimiter="\t")
                header = next(reader)
                row_count = sum(1 for _ in reader)
            lines.append(f"- 样本数: {len(header) - 1}")
            lines.append(f"- 基因数: {row_count}")

        lines.extend([
            f"",
            f"## 3. 质控指标",
            f"",
            f"- FastQC 报告已生成",
            f"- MultiQC 汇总报告已生成",
            f"",
            f"## 4. 后续建议",
            f"",
            f"1. 检查比对率是否 > 80%",
            f"2. 查看 MultiQC 报告确认样本质量",
            f"3. 使用差异表达分析流程比较条件间差异",
        ])
        return "\n".join(lines)

    def _wgs_report(self, task_id: str, output_dir: Path) -> str:
        lines = [
            f"# WGS 变异检测报告",
            f"",
            f"**任务ID**: `{task_id}`",
            f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"",
            f"## 1. 分析概要",
            f"",
        ]

        vcfs = list(output_dir.rglob("*.vcf.gz"))
        if vcfs:
            lines.append(f"### 输出文件")
            lines.append(f"")
            for v in vcfs:
                size_mb = v.stat().st_size / (1024 * 1024)
                lines.append(f"- `{v.name}` ({size_mb:.1f} MB)")

        flagstats = list(output_dir.rglob("*.flagstat"))
        if flagstats:
            lines.append(f"")
            lines.append(f"## 2. 比对统计")
            lines.append(f"")
            for fs in flagstats[:3]:
                content = fs.read_text(errors="ignore")
                for line in content.split("\n"):
                    if "mapped (" in line:
                        lines.append(f"- {line.strip()}")

        lines.extend([
            f"",
            f"## 3. 后续建议",
            f"",
            f"1. 使用 bcftools stats 统计变异类型分布",
            f"2. 使用 VEP/SnpEff 注释变异功能影响",
            f"3. 过滤低质量变异 (QUAL < 30, DP < 10)",
        ])
        return "\n".join(lines)

    def _de_report(self, task_id: str, output_dir: Path) -> str:
        lines = [
            f"# 差异表达分析报告",
            f"",
            f"**任务ID**: `{task_id}`",
            f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"",
        ]

        result_files = list(output_dir.rglob("*_results.csv"))
        if result_files:
            lines.append(f"## 1. 差异基因统计")
            lines.append(f"")
            lines.append(f"| 对比组 | 总基因数 | DEGs (padj<0.05) | 上调 | 下调 |")
            lines.append(f"|--------|---------|-----------------|------|------|")
            
            for rf in result_files:
                name = rf.stem.replace("_results", "")
                with open(rf) as f:
                    reader = csv.DictReader(f)
                    rows = list(reader)
                    total = len(rows)
                    sig = sum(1 for r in rows if r.get("padj") and float(r["padj"]) < 0.05)
                    up = sum(1 for r in rows if r.get("padj") and r.get("log2FoldChange") and float(r["padj"]) < 0.05 and float(r["log2FoldChange"]) > 0)
                    down = sig - up
                lines.append(f"| {name} | {total} | {sig} | {up} | {down} |")

        lines.extend([
            f"",
            f"## 2. 后续分析建议",
            f"",
            f"1. 绘制火山图和热图",
            f"2. 进行 GO/KEGG 通路富集分析",
            f"3. 关注 padj < 0.05 且 |log2FC| > 1 的基因",
        ])
        return "\n".join(lines)

    def _cnv_report(self, task_id: str, output_dir: Path) -> str:
        return self._generic_report(task_id, output_dir, "CNV 分析")

    def _metagenomics_report(self, task_id: str, output_dir: Path) -> str:
        lines = [
            f"# 宏基因组分类报告",
            f"",
            f"**任务ID**: `{task_id}`",
            f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"",
        ]

        reports = list(output_dir.rglob("*.bracken.species"))
        if reports:
            lines.append(f"## 1. 物种丰度 (Top 20)")
            lines.append(f"")
            for rp in reports[:1]:
                with open(rp) as f:
                    reader = csv.DictReader(f, delimiter="\t")
                    lines.append(f"| 物种 | Reads | 比例 |")
                    lines.append(f"|------|-------|------|")
                    for i, row in enumerate(reader):
                        if i >= 20:
                            break
                        lines.append(f"| {row.get('name', '')} | {row.get('new_est_reads', '')} | {row.get('fraction_total_reads', '')} |")

        return "\n".join(lines)

    def _qc_report(self, task_id: str, output_dir: Path) -> str:
        return self._generic_report(task_id, output_dir, "质量控制")

    def _generic_report(self, task_id: str, output_dir: Path, title: str = "分析") -> str:
        lines = [
            f"# {title}报告",
            f"",
            f"**任务ID**: `{task_id}`",
            f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"",
            f"## 输出文件",
            f"",
            f"```",
        ]
        
        for f in sorted(output_dir.rglob("*")):
            if f.is_file() and not f.name.startswith("."):
                rel = f.relative_to(output_dir)
                lines.append(f"{rel}")
        
        lines.extend([f"```", f"", f"分析已完成，请查看上述输出文件。"])
        return "\n".join(lines)


report_generator = ReportGenerator()