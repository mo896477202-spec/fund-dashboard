"""
AI 基金分析脚本
使用 DeepSeek API 读取 data.json，生成每日基金操作分析报告
输出 ai_report.json 供网页展示
"""

import json
import os
import sys
from datetime import datetime

# OpenAI 兼容接口（DeepSeek 兼容 OpenAI SDK）
try:
    from openai import OpenAI
except ImportError:
    print("请先安装 openai: pip install openai")
    sys.exit(1)


def load_fund_data(data_path="data.json"):
    """加载基金数据文件"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(script_dir, data_path)

    if not os.path.exists(full_path):
        print(f"❌ 数据文件不存在: {full_path}")
        return None

    with open(full_path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_prompt(data):
    """构建发送给 DeepSeek 的分析提示词"""
    funds = data.get("funds", [])
    summary = data.get("summary", {})
    update_time = data.get("update_time", "未知")

    fund_lines = []
    for f in funds:
        fund_lines.append(
            f"- {f['code']} {f['name']} ({f['type']}) "
            f"净值: {f['net_value']} "
            f"日涨跌: {f['daily_change_percent']:.2f}% "
            f"近1周: {f.get('week_change', 0):.2f}% "
            f"近1月: {f.get('month_change', 0):.2f}%"
        )

    prompt = f"""你是一位专业的基金投资顾问。请根据以下基金数据，给出今日的操作建议。

数据更新时间: {update_time}

持仓汇总:
- 持仓总额: {summary.get('total_value', 'N/A')}
- 今日收益: {summary.get('daily_change', 'N/A')}
- 总收益率: {summary.get('total_return_percent', 'N/A')}%

持仓基金明细:
{chr(10).join(fund_lines)}

请按以下 JSON 格式输出分析结果（严格 JSON，不要包含 markdown 标记）:

{{
    "overview": "一句话概括今日市场情况和操作策略",
    "signals": [
        {{
            "fund_code": "基金代码",
            "fund_name": "基金名称",
            "signal": "buy/hold/sell",
            "reason": "给出操作建议的详细理由，结合涨跌、趋势、估值等"
        }}
    ],
    "risk_note": "风险提示，如有需要注意的风险请说明，没有则填无"
}}

分析要点:
1. signal 字段只能为 buy（买入/加仓）、hold（持有观望）、sell（卖出/减仓）
2. 结合近1周和近1月的涨跌趋势判断
3. 考虑估值水平（是否有泡沫风险）
4. 注意行业分散度，避免过度集中在同一板块
5. 场外基金当天15:00前操作以当天净值为准，ETF可盘中操作
6. reason 要具体，不要泛泛而谈"""

    return prompt


def call_deepseek(prompt, api_key, base_url="https://api.deepseek.com"):
    """调用 DeepSeek API 进行分析"""
    client = OpenAI(api_key=api_key, base_url=base_url)

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": "你是一位专业的基金投资分析师，擅长技术分析和基本面分析。请始终用JSON格式回复。"},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=2000,
        response_format={"type": "json_object"}
    )

    return response.choices[0].message.content


def parse_response(content):
    """解析 DeepSeek 返回的 JSON"""
    try:
        result = json.loads(content)
        return result
    except json.JSONDecodeError:
        # 尝试从文本中提取 JSON
        import re
        match = re.search(r'\{[\s\S]*\}', content)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        return None


def main():
    # 从环境变量获取 API Key
    api_key = os.environ.get("DEEPSEEK_API_KEY") or os.environ.get("OPENAI_API_KEY")
    base_url = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")

    if not api_key:
        print("❌ 请设置环境变量 DEEPSEEK_API_KEY")
        print("   export DEEPSEEK_API_KEY=sk-xxxxx")
        sys.exit(1)

    # 加载数据
    data = load_fund_data()
    if not data:
        sys.exit(1)

    print(f"===== AI 基金分析开始 [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] =====")
    print(f"数据更新时间: {data.get('update_time')}")
    print(f"基金数量: {len(data.get('funds', []))}")

    # 构建提示词
    prompt = build_prompt(data)

    # 调用 DeepSeek
    print("\n正在调用 DeepSeek 进行分析...")
    try:
        raw_response = call_deepseek(prompt, api_key, base_url)
        analysis = parse_response(raw_response)

        if not analysis:
            print("❌ 无法解析 AI 返回结果")
            print(f"原始返回: {raw_response}")
            sys.exit(1)

        print("✓ AI 分析完成")

    except Exception as e:
        print(f"❌ AI 分析失败: {e}")
        sys.exit(1)

    # 构建最终报告
    report = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "data_update_time": data.get("update_time"),
        "overview": analysis.get("overview", ""),
        "signals": analysis.get("signals", []),
        "risk_note": analysis.get("risk_note", ""),
        "raw_funds_snapshot": [
            {
                "code": f["code"],
                "name": f["name"],
                "net_value": f["net_value"],
                "daily_change_percent": f["daily_change_percent"],
                "month_change": f.get("month_change", 0),
            }
            for f in data.get("funds", [])
        ]
    }

    # 写入文件
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, "ai_report.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\n===== 报告已写入 {output_path} =====")

    # 打印摘要
    print(f"\n📊 操作建议摘要:")
    for s in report["signals"]:
        emoji = {"buy": "🟢", "hold": "🟡", "sell": "🔴"}.get(s.get("signal"), "⚪")
        print(f"  {emoji} {s.get('fund_name', 'N/A')}: {s.get('signal', 'N/A').upper()} - {s.get('reason', '')}")

    if report.get("risk_note") and report["risk_note"] != "无":
        print(f"\n⚠️ 风险提示: {report['risk_note']}")


if __name__ == "__main__":
    main()
