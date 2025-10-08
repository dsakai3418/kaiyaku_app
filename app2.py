import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(layout="wide") # レイアウトを広げる

st.title("Camel 契約管理・請求計算システム")
st.markdown("---")

# --- 1. ファイルアップロードセクション ---
with st.expander("CSVファイルをアップロード"):
    col1, col2 = st.columns(2)
    with col1:
        np_csv_file = st.file_uploader("NP CSVをアップロード", type=["csv"], key="np_csv")
        np_df = None
        if np_csv_file:
            np_df = pd.read_csv(np_csv_file)
            st.write("NP CSV (一部):")
            st.dataframe(np_df.head())
    with col2:
        bakuraku_csv_file = st.file_uploader("バクラク CSVをアップロード", type=["csv"], key="bakuraku_csv")
        bakuraku_df = None
        if bakuraku_csv_file:
            bakuraku_df = pd.read_csv(bakuraku_csv_file)
            st.write("バクラク CSV (一部):")
            st.dataframe(bakuraku_df.head())
st.markdown("---")

# --- 2. 未入金金額計算セクション ---
st.header("未入金金額計算")
total_billed_amount = 0

# NP CSVからの請求金額合計
np_billed_amount = 0
if np_df is not None and '請求金額' in np_df.columns:
    np_billed_amount = np_df['請求金額'].sum()
    st.info(f"NPからの請求金額合計: {np_billed_amount:,.0f}円")
    total_billed_amount += np_billed_amount

# バクラク CSVからの請求金額合計
bakuraku_billed_amount = 0
if bakuraku_df is not None and '金額' in bakuraku_df.columns:
    # バクラクCSVには複数の「金額」系カラムがあるので、どの「金額」を使用するか検討が必要
    # 例として、ここでは「金額」カラムを合計する
    bakuraku_billed_amount = bakuraku_df['金額'].sum()
    st.info(f"バクラクからの請求金額合計: {bakuraku_billed_amount:,.0f}円")
    total_billed_amount += bakuraku_billed_amount

st.subheader("入金状況入力")
paid_amount = st.number_input("入金額を入力してください", min_value=0, value=0, step=1000, key="paid_amount")

unpaid_amount = total_billed_amount - paid_amount
payment_status_text = "未入金" if unpaid_amount > 0 else "入金済み" if unpaid_amount == 0 else "過払い"

st.metric(label="現在の未入金金額", value=f"{unpaid_amount:,.0f}円", delta_color="inverse")
st.markdown(f"**支払い状況:** {payment_status_text}")
st.markdown("---")


# --- 3. 契約残存期間計算セクション ---
st.header("契約残存期間計算")

st.subheader("契約情報入力")
contract_start_date = st.date_input("Camel契約開始日を選択してください", value=datetime.today(), key="contract_start_date")

st.subheader("休業期間設定")
# 複数休業期間に対応するため、st.session_state を利用
if 'holiday_periods' not in st.session_state:
    st.session_state.holiday_periods = []

# 新しい休業期間追加用フォーム
col_h_start, col_h_end, col_h_add = st.columns([0.4, 0.4, 0.2])
with col_h_start:
    new_holiday_start = st.date_input("新しい休業期間開始日", value=None, key="new_holiday_start")
with col_h_end:
    new_holiday_end = st.date_input("新しい休業期間終了日", value=None, key="new_holiday_end")
with col_h_add:
    st.write("") # スペーサー
    if st.button("休業期間を追加", key="add_holiday_btn"):
        if new_holiday_start and new_holiday_end and new_holiday_start <= new_holiday_end:
            st.session_state.holiday_periods.append((new_holiday_start, new_holiday_end))
            st.success(f"休業期間 {new_holiday_start.strftime('%Y/%m/%d')}〜{new_holiday_end.strftime('%Y/%m/%d')} を追加しました。")
        else:
            st.error("有効な休業期間を入力してください。")

# 登録済みの休業期間を表示
if st.session_state.holiday_periods:
    st.markdown("**登録済みの休業期間:**")
    for i, (h_start, h_end) in enumerate(st.session_state.holiday_periods):
        st.write(f"- {h_start.strftime('%Y/%m/%d')} 〜 {h_end.strftime('%Y/%m/%d')}")
    if st.button("全ての休業期間をクリア", key="clear_holidays_btn"):
        st.session_state.holiday_periods = []
        st.experimental_rerun() # 画面を再描画してリストを更新

st.subheader("解約情報入力")
col_cancel_year, col_cancel_month = st.columns(2)
with col_cancel_year:
    cancel_year = st.number_input("解約希望年", min_value=datetime.today().year, value=datetime.today().year, key="cancel_year")
with col_cancel_month:
    cancel_month = st.number_input("解約希望月", min_value=1, max_value=12, value=datetime.today().month, key="cancel_month")
billing_unit_price = st.number_input("請求単価", min_value=0, value=10000, step=1000, key="billing_unit_price")

st.markdown("---")

# --- 4. 最終出力フォーマット表示セクション ---
st.header("計算結果")

# ここに計算ロジックを実装
# 契約残存期間計算のロジックは複雑なため、ここでは仮の値を設定
# 実際の実装では、contract_start_date, st.session_state.holiday_periods, cancel_year, cancel_month を使って正確に計算します。

# 最短解約日（契約期間）の計算ロジック（仮）
# 6ヶ月ごとの自動更新と休業期間を考慮
def calculate_min_cancel_date_contract(start_date, holiday_periods):
    current_date = start_date
    initial_contract_end = start_date + timedelta(days=180) # 6ヶ月後（おおよそ）

    # 休業期間による契約期間の延伸を計算
    total_holiday_days = 0
    for h_start, h_end in holiday_periods:
        # 休業期間が契約期間内に含まれるか、または契約期間をまたぐ場合を考慮
        overlap_start = max(current_date, h_start)
        overlap_end = min(initial_contract_end, h_end) # ここは慎重に考慮が必要
        if overlap_start <= overlap_end:
            total_holiday_days += (overlap_end - overlap_start).days + 1
            
    # シンプル化のため、ここでは直接6ヶ月後を計算
    # 実際は、契約開始日から6ヶ月毎の区切りを見つけ、休業期間を差し引く必要がある
    # 例: 契約期間の終わりが休業期間と重なる場合、その分後ろにずらす
    
    # 非常に簡略化されたロジック（実際はもっと複雑）
    min_cancel_date = start_date
    while min_cancel_date < datetime.today().date(): # 現在よりも未来の契約終了日を見つける
        min_cancel_date = min_cancel_date.replace(month=(min_cancel_date.month % 12) + 1, day=1) # 1ヶ月進める
        if min_cancel_date.month == start_date.month and min_cancel_date.year > start_date.year: # 6ヶ月サイクル
            # 6ヶ月更新ロジックをここに
            pass
            
    # ここでは仮に、契約開始から一番近い6ヶ月後の月末を最短解約日（契約期間）とする
    # より正確なロジックが必要
    min_cancel_date_contract = (contract_start_date + pd.DateOffset(months=6)).replace(day=1) - pd.DateOffset(days=1)
    
    # 休業期間による延長は、契約期間の終わりに日数を加算する形で実装
    # 例: min_cancel_date_contract + timedelta(days=total_holiday_days)
    
    return min_cancel_date_contract.date() if isinstance(min_cancel_date_contract, pd.Timestamp) else min_cancel_date_contract

# 最短解約日（申告日）の計算ロジック（仮）
def calculate_min_cancel_date_declared(cancel_year, cancel_month, holiday_periods):
    try:
        declared_cancel_date = datetime(cancel_year, cancel_month, 1).date() # 解約希望月の1日
        
        # 休業期間を考慮して、申告日が後ろにずれる可能性を考慮する
        # ここも、上記と同様に複雑な日付計算が必要
        
        return declared_cancel_date
    except ValueError:
        return None

# 計算ボタン
if st.button("計算を実行", key="execute_calculation_btn"):
    # 各計算結果を保持する変数
    formatted_contract_start_date = contract_start_date.strftime('%Y/%m/%d')
    
    holiday_periods_str_list = [f"{s.strftime('%Y/%m/%d')}〜{e.strftime('%Y/%m/%d')}" for s, e in st.session_state.holiday_periods]
    formatted_holiday_periods = ", ".join(holiday_periods_str_list) if holiday_periods_str_list else "設定なし"
    
    # 契約残存期間の計算
    calculated_min_cancel_date_contract = calculate_min_cancel_date_contract(contract_start_date, st.session_state.holiday_periods)
    calculated_min_cancel_date_declared = calculate_min_cancel_date_declared(cancel_year, cancel_month, st.session_state.holiday_periods)
    
    # 残存期間と請求金額の計算（仮）
    if calculated_min_cancel_date_declared:
        today = datetime.today().date()
        remaining_months_rough = ((calculated_min_cancel_date_declared.year - today.year) * 12 + calculated_min_cancel_date_declared.month - today.month)
        if remaining_months_rough < 0:
            remaining_months_rough = 0
        payment_plan_amount = billing_unit_price * remaining_months_rough
    else:
        remaining_months_rough = 0
        payment_plan_amount = 0


    st.write(f"◆ Camel契約開始日：{formatted_contract_start_date}")
    st.write(f"◆ 休業期間：{formatted_holiday_periods}")
    st.write(f"◆ 最短解約日（契約期間）：{calculated_min_cancel_date_contract.strftime('%Y/%m/%d') if calculated_min_cancel_date_contract else 'N/A'}")
    st.write(f"◆ 最短解約日（申告日）：{calculated_min_cancel_date_declared.strftime('%Y/%m/%d') if calculated_min_cancel_date_declared else 'N/A'}")
    st.write(f"◆ 支払い状況：{unpaid_amount:,.0f}円 （{payment_status_text}）")
    st.write(f"◆ 支払計画：{payment_plan_amount:,.0f}円 （残存{remaining_months_rough}ヶ月）")