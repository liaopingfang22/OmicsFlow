"""Results Interpreter Agent - Interprets analysis results and generates reports."""
import csv, json, logging
from pathlib import Path
logger = logging.getLogger("omicsflow.agent.results_interpreter")

class ResultsInterpreterAgent:
    async def interpret(self, task_id: str, pipeline_type: str, output_dir: str) -> dict:
        result = {"task_id": task_id, "pipeline_type": pipeline_type, "summary": "", "key_findings": [], "qc_status": "pass", "recommendations": []}
        out = Path(output_dir)
        if not out.exists(): return result
        interpreters = {"rnaseq": self._interp_rnaseq, "de": self._interp_de, "wgs": self._interp_wgs, "amplicon": self._interp_amplicon, "metagenomics": self._interp_metagenomics}
        interp = interpreters.get(pipeline_type, self._interp_generic)
        extra = interp(out)
        result.update(extra)
        return result

    def _interp_de(self, out: Path) -> dict:
        findings, recs = [], []
        for f in out.rglob("*_results.csv"):
            try:
                with open(f) as fh:
                    rows = list(csv.DictReader(fh))
                    total = len(rows)
                    sig = sum(1 for r in rows if r.get("padj") and float(r["padj"]) < 0.05)
                    up = sum(1 for r in rows if r.get("padj") and r.get("log2FoldChange") and float(r["padj"]) < 0.05 and float(r["log2FoldChange"]) > 0)
                    down = sig - up
                    findings.append(f"{f.stem}: {sig}/{total} DEGs (padj<0.05), {up} 上调, {down} 下调")
                    if sig > 100: recs.append("发现大量差异基因，建议进行 GO/KEGG 通路富集分析")
                    elif sig > 0: recs.append("建议关注 padj<0.05 且 |log2FC|>1 的高置信基因")
                    else: recs.append("未发现显著差异基因，建议检查实验设计或调整阈值")
            except: pass
        return {"summary": f"差异表达分析完成", "key_findings": findings, "recommendations": recs}

    def _interp_rnaseq(self, out: Path) -> dict:
        findings = []
        for f in out.rglob("*.Log.final.out"):
            try:
                for line in f.read_text().split("\n"):
                    if "Uniquely mapped reads %" in line:
                        pct = line.split("|")[-1].strip()
                        findings.append(f"唯一比对率: {pct}")
                        try:
                            v = float(pct.replace("%",""))
                            if v < 80: return {"key_findings": findings, "qc_status": "warn", "recommendations": ["比对率低于80%，检查参考基因组是否匹配"]}
                        except: pass
            except: pass
        return {"summary": "RNA-seq 分析完成", "key_findings": findings, "recommendations": ["检查 MultiQC 报告确认整体质量", "建议使用差异表达管线比较条件间差异"]}

    def _interp_wgs(self, out: Path) -> dict:
        findings = []
        for f in out.rglob("*.flagstat"):
            try:
                for line in f.read_text().split("\n"):
                    if "mapped (" in line: findings.append(line.strip())
            except: pass
        return {"summary": "WGS 变异检测完成", "key_findings": findings, "recommendations": ["使用 bcftools stats 统计变异类型", "使用 VEP/SnpEff 注释变异"]}

    def _interp_amplicon(self, out: Path) -> dict:
        findings = []
        for f in out.rglob("asv_summary.tsv"):
            try:
                with open(f) as fh:
                    reader = csv.DictReader(fh, delimiter='\t')
                    for row in reader:
                        findings.append(f"总 ASV 数: {row.get('Total_ASVs','?')}, 总 Reads: {row.get('Total_Reads','?')}")
            except: pass
        return {"summary": "16S/ITS 扩增子分析完成", "key_findings": findings, "recommendations": ["检查稀释曲线确认测序深度", "比较组间 α/β 多样性差异"]}

    def _interp_metagenomics(self, out: Path) -> dict:
        return {"summary": "宏基因组分类完成", "key_findings": [], "recommendations": ["查看 Bracken 物种丰度报告", "比较组间差异物种"]}

    def _interp_generic(self, out: Path) -> dict:
        files = [str(f.relative_to(out)) for f in out.rglob("*") if f.is_file() and not f.name.startswith(".")]
        return {"summary": "分析完成", "key_findings": [f"共生成 {len(files)} 个输出文件"], "recommendations": ["查看输出文件了解分析结果"]}

results_interpreter = ResultsInterpreterAgent()
