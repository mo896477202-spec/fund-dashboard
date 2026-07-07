"""
基金数据抓取脚本
支持场外开放式基金 + 场内ETF
使用 akshare 抓取基金净值、历史数据，输出 data.json
"""

import akshare as ak
import json
import os
from datetime import datetime, timedelta

# ===== 配置：你的基金列表 =====
OTC_FUNDS = ["021031", "012349", "006328"]  # 场外基金
ETF_FUNDS = ["159570", "520920", "513050"]  # 场内ETF

# ===== 辅助函数 =====
def get_fund_name(code, fund_type):
    """尝试获取基金名称，失败则用代码作为名称"""
    name_map = {
        "021031": "天弘中证红利低波100联接C",
        "012349": "天弘中证光伏产业指数C",
        "006328": "易方达中概互联网ETF联接C",
        "159570": "港股通互联网ETF",
        "520920": "恒生科技ETF",
        "513050": "中概互联网ETF",
    }
    return name_map.get(code, f"基金{code}")


def fetch_otc_fund(code):
    """抓取场外开放式基金数据"""
    try:
        # 获取基金基本信息
        info_df = ak.fund_open_fund_info_em(symbol=code, indicator="单位净值走势")
        if info_df is None or info_df.empty:
            print(f"  [{code}] 未获取到场外基金数据")
            return None

        # 最新净值和前一日净值
        latest = info_df.iloc[-1]
        prev = info_df.iloc[-2] if len(info_df) > 1 else latest

        net_value = float(latest["单位净值"])
        prev_value = float(prev["单位净值"])
        daily_change = round((net_value - prev_value) / prev_value * 100, 2) if prev_value != 0 else 0

        # 历史净值（用于图表）
        # 取最近的数据用于走势图
        nav_history = []
        for _, row in info_df.tail(120).iterrows():
            nav_history.append({
                "date": str(row.name)[:10] if hasattr(row.name, '__str__') else str(row.get("净值日期", ""))[:10],
                "value": round(float(row["单位净值"]), 4)
            })

        # 计算周期涨跌
        today = datetime.now()
        def calc_period_change(days):
            if len(info_df) <= days:
                idx = 0
            else:
                idx = len(info_df) - days - 1
            old_val = float(info_df.iloc[idx]["单位净值"])
            return round((net_value - old_val) / old_val * 100, 2) if old_val != 0 else 0

        return {
            "code": code,
            "name": get_fund_name(code, "otc"),
            "type": "otc",
            "net_value": round(net_value, 4),
            "acc_net_value": round(float(latest.get("累计净值", net_value)), 4),
            "daily_change_percent": daily_change,
            "week_change": calc_period_change(5),
            "month_change": calc_period_change(22),
            "nav_history": nav_history
        }
    except Exception as e:
        print(f"  [{code}] 场外基金抓取异常: {e}")
        return None


def fetch_etf_fund(code):
    """抓取场内ETF数据"""
    try:
        # ETF实时行情
        fund_df = ak.fund_etf_fund_daily_em()
        if fund_df is None or fund_df.empty:
            print(f"  [{code}] 未获取到ETF列表数据")
            return None

        # 匹配代码
        match = fund_df[fund_df["基金代码"] == code]
        if match.empty:
            print(f"  [{code}] 未在ETF列表中找到该代码")
            return None

        row = match.iloc[0]
        net_value = float(row.get("单位净值", 0))

        # 日涨跌幅
        daily_change = float(row.get("日增长率", 0)) if "日增长率" in row else 0

        # 尝试获取历史净值数据
        nav_history = []
        try:
            hist_df = ak.fund_etf_hist_em(symbol=code, period="daily", start_date=(datetime.now() - timedelta(days=180)).strftime("%Y%m%d"), end_date=datetime.now().strftime("%Y%m%d"), adjust="")
            if hist_df is not None and not hist_df.empty:
                for _, hrow in hist_df.tail(120).iterrows():
                    nav_history.append({
                        "date": str(hrow["日期"])[:10],
                        "value": round(float(hrow["收盘"]), 4)
                    })
        except Exception as e:
            print(f"  [{code}] ETF历史数据抓取异常: {e}")

        # 计算周期涨跌
        week_change = 0
        month_change = 0
        if len(nav_history) >= 5:
            week_change = round((net_value - nav_history[-6]["value"]) / nav_history[-6]["value"] * 100, 2)
        if len(nav_history) >= 22:
            month_change = round((net_value - nav_history[-23]["value"]) / nav_history[-23]["value"] * 100, 2)

        return {
            "code": code,
            "name": get_fund_name(code, "etf"),
            "type": "etf",
            "net_value": round(net_value, 4),
            "acc_net_value": round(net_value, 4),
            "daily_change_percent": round(daily_change, 2),
            "week_change": week_change,
            "month_change": month_change,
            "nav_history": nav_history
        }
    except Exception as e:
        print(f"  [{code}] ETF抓取异常: {e}")
        return None


def main():
    print(f"===== 基金数据抓取开始 [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] =====")

    funds_data = []

    # 抓取场外基金
    print("\n--- 场外基金 ---")
    for code in OTC_FUNDS:
        print(f"抓取 {code}...")
        data = fetch_otc_fund(code)
        if data:
            funds_data.append(data)
            print(f"  ✓ {data['name']} 净值: {data['net_value']} 涨跌: {data['daily_change_percent']}%")

    # 抓取场内ETF
    print("\n--- 场内ETF ---")
    for code in ETF_FUNDS:
        print(f"抓取 {code}...")
        data = fetch_etf_fund(code)
        if data:
            funds_data.append(data)
            print(f"  ✓ {data['name']} 净值: {data['net_value']} 涨跌: {data['daily_change_percent']}%")

    if not funds_data:
        print("❌ 没有成功抓取任何基金数据！")
        return

    # 计算汇总
    total_value = sum(f["net_value"] for f in funds_data) * 1000  # 假设每只持仓1000份
    daily_change_total = sum(f["net_value"] * 1000 * f["daily_change_percent"] / 100 for f in funds_data)
    daily_change_percent = round(daily_change_total / total_value * 100, 2) if total_value != 0 else 0
    fund_count = len(funds_data)
    otc_count = sum(1 for f in funds_data if f["type"] == "otc")
    etf_count = sum(1 for f in funds_data if f["type"] == "etf")

    result = {
        "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "summary": {
            "total_value": round(total_value, 2),
            "daily_change": round(daily_change_total, 2),
            "daily_change_percent": daily_change_percent,
            "total_return": 0,
            "total_return_percent": 0,
            "fund_count": fund_count,
            "otc_count": otc_count,
            "etf_count": etf_count
        },
        "funds": funds_data
    }

    # 写入文件
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n===== 完成！数据已写入 {output_path} =====")
    print(f"共 {fund_count} 只基金，总净值 {total_value:.2f}")


if __name__ == "__main__":
    main()
