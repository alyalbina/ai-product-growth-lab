"""Build a distinct, attribution-preserving real-data evidence page."""

import json
from pathlib import Path

import pandas as pd
import plotly.express as px
from plotly.offline import get_plotlyjs


def build():
    result = json.loads(Path("data/external/analysis.json").read_text(encoding="utf-8"))
    figs = []
    for field in ["VisitorType", "TrafficType", "Month"]:
        frame = pd.DataFrame(result["groups"][field])
        fig = px.bar(frame, x="group", y="conversion", error_y=frame.ci_high-frame.conversion,
                     error_y_minus=frame.conversion-frame.ci_low,
                     color_discrete_sequence=["#087f82"], hover_data=["sessions", "purchases"],
                     labels={"conversion": "Session purchase rate", "group": field})
        fig.update_layout(height=350, paper_bgcolor="#fbfaf7", plot_bgcolor="#fbfaf7",
                          margin={"l": 30, "r": 20, "t": 20, "b": 40})
        fig.update_yaxes(tickformat=".0%")
        figs.append(f"<section><h2>{field} / descriptive association</h2>"+
                    fig.to_html(full_html=False, include_plotlyjs=False)+"</section>")
    html = f"""<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Independent UCI session study</title><style>body{{margin:0;background:#fbfaf7;color:#19383a;font:16px/1.65 Arial}}main{{max-width:1000px;margin:auto;padding:40px 24px}}h1{{font-size:44px;line-height:1.1;letter-spacing:-2px}}h2{{font-size:24px}}section{{padding:28px 0;border-top:1px solid #d5dfda}}.notice{{padding:12px;background:#e6eee8;font-weight:600}}a{{color:#087f82}}p{{max-width:850px}}code{{overflow-wrap:anywhere}}</style><main><a href="index.html">← Product case study</a><p class="notice">Real public dataset — independent e-commerce analysis</p><h1>Different data.<br>Different evidence.</h1><p><strong>{result['sessions']:,} sessions · {result['purchases']:,} purchase sessions · {result['conversion']:.2%} purchase rate.</strong><br>95% Wilson interval: {result['ci_low']:.2%}–{result['ci_high']:.2%}.</p><p>C. Sakar &amp; Y. Kastro (2018), <em>Online Shoppers Purchasing Intention Dataset</em>, UCI Machine Learning Repository. <a href="https://doi.org/10.24432/C5F88Q">DOI 10.24432/C5F88Q</a>. <a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a>. Downloaded 9 October 2026. Original measurements retained; aggregate analyses and graphics added by this project.</p><p>Measured missing cells: {result['missing_cells']}. Identical feature rows: {result['identical_feature_rows']}, retained because there is no identity key to confirm duplicate sessions. Product-page duration maximum {result['numeric_outliers']['ProductRelated_Duration']['max']:,.1f}, compared with p99 {result['numeric_outliers']['ProductRelated_Duration']['p99']:,.1f}; extremes are reported rather than silently trimmed.</p><p class="notice">These associations cannot estimate an AI reward effect.</p><p>The purchase label Revenue is Boolean, not dollars. No durable IDs, exact timestamps, ordered event stream or transaction amounts are supplied. Retention, ordered funnels, ARPU and experiment lift cannot be estimated. Returning_Visitor is a recorded source category, not a measured repeated visit in this file. PageValues can contain outcome-related information, so it is unsuitable for pre-treatment causal adjustment.</p><p>Charts show descriptive subgroup conversion and individual Wilson intervals. Small traffic categories are visibly uncertain. Month names are source categories in an unspecified historical year; they do not describe a current time series. Differences may reflect selection and confounding, and are never transferred to the AI SaaS simulation.</p>"""
    html += "<script>"+get_plotlyjs()+"</script>"+"".join(figs)
    html += f"<p>Original CSV SHA-256:<br><code>{result['sha256']}</code></p><p>Reproduce with <code>python -m scripts.external</code> and <code>python -m scripts.external_report</code>. Original source, attribution and separate analysis JSON are included in the project package.</p></main></html>"
    Path("case-study/external.html").write_text(html, encoding="utf-8")
    case = Path("case-study/index.html")
    text = case.read_text(encoding="utf-8")
    if 'href="external.html"' not in text:
        text = text.replace('<a href="https://archive.ics.uci.edu/dataset/', '<a href="external.html">Explore the independent real-data study ↗</a><br><a href="https://archive.ics.uci.edu/dataset/', 1)
        case.write_text(text, encoding="utf-8")
    print("Created separate real-data page with three interactive figures")


if __name__ == "__main__":
    build()
