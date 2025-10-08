import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import locale

# ロケールを日本語に設定 (ただし、st.date_inputの表示には影響しないことが多い)
try:
    locale.setlocale(locale.LC_ALL, 'ja_JP.UTF-8')
except locale.Error:
    st.warning("日本語ロケールの設定に失敗しました。日付の書式などが英語になる場合があります。")

st.set_page_config(layout="wide")

st.title("Camel 契約管理・請求計算システム")
st.markdown("---")

# --- 1. ファイルアップロードセクション ---
st.header("CSVファイルアップロード")
upload_col1, upload_col2 = st.columns(2)

np_df = None
bakuraku_df = None

with upload_col1:
    st.subheader("NP CSV")
    np_csv_file = st.file_uploader("NPからの請求CSVをここにドラッグ＆ドロップ、またはファイルを選択", type=["csv"], key="np_csv")
    if np_csv_file:
        try:
            np_df = pd.read_csv(np_csv_file)
            st.success("NP CSVを正常に読み込みました。")
            if '請求金額' not in np_df.columns:
                st.warning("NP CSVに'請求金額'カラムが見つかりません。計算に影響する可能性があります。")
            st.expander("NP CSVプレビュー").dataframe(np_df.head())
        except Exception as e:
            st.error(f"NP CSVの読み込み中にエラーが発生しました: {e}")

with upload_col2:
    st.subheader("バクラク CSV")
    bakuraku_csv_file = st.file_uploader("バクラクからの請求CSVをここにドラッグ＆ドロップ、またはファイルを選択", type=["csv"], key="bakuraku_csv")
    if bakuraku_csv_file:
        try:
            bakuraku_df = pd.read_csv(bakuraku_csv_file)
            st.success("バクラク CSVを正常に読み込みました。")
            if '金額' not in bakuraku_df.columns:
                st.warning("バクラク CSVに'金額'カラムが見つかりません。計算に影響する可能性があります。")
            st.expander("バクラク CSVプレビュー").dataframe(bakuraku_df.head())
        except Exception as e:
            st.error(f"バクラク CSVの読み込み中にエラーが発生しました: {e}")
st.markdown("---")


# --- 2. 未入金金額計算セクション ---
st.header("未入金金額計算")
total_billed_amount = 0

np_billed_amount = 0
if np_df is not None and '請求金額' in np_df.columns:
    np_billed_amount = np_df['請求金額'].sum()
    st.info(f"**NPからの請求金額合計:** {np_billed_amount:,.0f}円")
    total_billed_amount += np_billed_amount
else:
    st.info("NP CSVが未アップロード、または請求金額カラムが見つかりません。")

bakuraku_billed_amount = 0
if bakuraku_df is not None and '金額' in bakuraku_df.columns: # ここは必要に応じてカラム名を調整してください
    bakuraku_billed_amount = bakuraku_df['金額'].sum()
    st.info(f"**バクラクからの請求金額合計:** {bakuraku_billed_amount:,.0f}円")
    total_billed_amount += bakuraku_billed_amount
else:
    st.info("バクラク CSVが未アップロード、または金額カラムが見つかりません。")

st.subheader("入金状況入力")
paid_amount = st.number_input("入金額を入力してください", min_value=0, value=0, step=1000, key="paid_amount", help="手入力で入金された金額を入力します。")

unpaid_amount = total_billed_amount - paid_amount
payment_status_text = "未入金" if unpaid_amount > 0 else "入金済み" if unpaid_amount == 0 else "過払い"

st.metric(label="現在の未入金金額", value=f"{unpaid_amount:,.0f}円", delta_color="inverse")
st.markdown(f"**支払い状況:** {payment_status_text}")
st.markdown("---")


# --- 3. 契約残存期間計算セクション ---
st.header("契約残存期間計算")

st.subheader("契約情報入力")
contract_start_date = st.date_input("Camel契約開始日を選択してください", value=datetime.today(), key="contract_start_date", format="YYYY/MM/DD")

st.subheader("休業期間設定")
if 'holiday_periods' not in st.session_state:
    st.session_state.holiday_periods = []

col_h_start, col_h_end, col_h_add = st.columns([0.4, 0.4, 0.2])
with col_h_start:
    new_holiday_start = st.date_input("新しい休業期間開始日", value=None, key="new_holiday_start", format="YYYY/MM/DD")
with col_h_end:
    new_holiday_end = st.date_input("新しい休業期間終了日", value=None, key="new_holiday_end", format="YYYY/MM/DD")
with col_h_add:
    st.write("") # スペーサー
    st.write("") # スペーサー
    if st.button("休業期間を追加", key="add_holiday_btn"):
        if new_holiday_start and new_holiday_end and new_holiday_start <= new_holiday_end:
            st.session_state.holiday_periods.append((new_holiday_start, new_holiday_end))
            st.success(f"休業期間 {new_holiday_start.strftime('%Y/%m/%d')}〜{new_holiday_end.strftime('%Y/%m/%d')} を追加しました。")
        else:
            st.error("有効な休業期間を入力してください（開始日≦終了日）。")
        # 追加後にフォームをクリアして再入力しやすくする
        st.session_state.new_holiday_start = None
        st.session_state.new_holiday_end = None
        st.experimental_rerun() # 画面を再描画してリストを更新

# 登録済みの休業期間を表示
if st.session_state.holiday_periods:
    st.markdown("**現在の登録済み休業期間:**")
    for i, (h_start, h_end) in enumerate(st.session_state.holiday_periods):
        st.write(f"- {h_start.strftime('%Y/%m/%d')} 〜 {h_end.strftime('%Y/%m/%d')}")
    if st.button("全ての休業期間をクリア", key="clear_holidays_btn"):
        st.session_state.holiday_periods = []
        st.experimental_rerun()

st.subheader("解約情報入力")
col_cancel_year, col_cancel_month = st.columns(2)
with col_cancel_year:
    cancel_year = st.number_input("解約希望年", min_value=datetime.today().year, value=datetime.today().year, key="cancel_year")
with col_cancel_month:
    cancel_month = st.number_input("解約希望月", min_value=1, max_value=12, value=datetime.today().month, key="cancel_month")
billing_unit_price = st.number_input("請求単価", min_value=0, value=10000, step=1000, key="billing_unit_price", help="残存期間分の請求金額計算に使用する単価です。")

st.markdown("---")

# --- 4. 最終出力フォーマット表示セクション ---
st.header("計算結果")

# --- 計算ロジック（仮実装） ---
# ここに正確な計算ロジックを実装してください。
# `st.date_input` の `value` は `datetime.date` オブジェクトを返します。
# したがって、日付計算は `datetime` モジュールを使って行います。

# 最短解約日（契約期間）の計算ロジック（仮）
def calculate_min_cancel_date_contract_logic(start_date: datetime.date, holiday_periods: list):
    # 契約開始日から最初の6ヶ月更新日
    first_renewal_date = (pd.to_datetime(start_date) + pd.DateOffset(months=6)).date()

    # 現在の契約サイクル終了日を特定
    current_contract_end = start_date
    while current_contract_end < datetime.today().date():
        current_contract_end = (pd.to_datetime(current_contract_end) + pd.DateOffset(months=6)).date()
        
    # 休業期間による契約期間の延伸（簡易的な実装）
    # 実際のロジックは、休業期間が契約期間のどの部分にかかるかを考慮して複雑になります
    total_holiday_days_offset = 0
    for h_start, h_end in holiday_periods:
        # 休業期間の重複を考慮した日数計算が必要
        # ここでは単純に、契約終了日以降に発生する休業日数を加算する形を仮定
        if h_start > current_contract_end: # 契約期間終了後に発生する休業期間
            total_holiday_days_offset += (h_end - h_start).days + 1

    final_contract_end_date = current_contract_end + timedelta(days=total_holiday_days_offset)
    
    # 契約サイクル終了日の月末に調整（例）
    final_contract_end_date = (pd.to_datetime(final_contract_end_date) + pd.DateOffset(months=1)).replace(day=1) - pd.DateOffset(days=1)
    
    return final_contract_end_date.date()

# 最短解約日（申告日）の計算ロジック（仮）
def calculate_min_cancel_date_declared_logic(cancel_year: int, cancel_month: int, holiday_periods: list):
    try:
        declared_cancel_date = datetime(cancel_year, cancel_month, 1).date() # 解約希望月の1日
        
        # 休業期間による申告日の延伸（簡易的な実装）
        # 例えば、申告月が休業期間と重なる場合、その日数分後ろにずらす
        total_holiday_days_offset = 0
        for h_start, h_end in holiday_periods:
            if h_start <= declared_cancel_date <= h_end: # 申告日が休業期間内にある場合
                total_holiday_days_offset += (h_end - declared_cancel_date).days + 1
            elif h_start < declared_cancel_date and h_end >= declared_cancel_date:
                total_holiday_days_offset += (h_end - declared_cancel_date).days + 1 # 申告日以降の休業期間

        final_declared_cancel_date = declared_cancel_date + timedelta(days=total_holiday_days_offset)
        
        # 申告日の月末に調整（例）
        final_declared_cancel_date = (pd.to_datetime(final_declared_cancel_date) + pd.DateOffset(months=1)).replace(day=1) - pd.DateOffset(days=1)
        
        return final_declared_cancel_date.date()
    except ValueError:
        return None

# 計算ボタン
if st.button("全ての計算を実行", key="execute_calculation_btn", type="primary"):
    with st.spinner('計算中...しばらくお待ちください。'):
        # 各計算結果を保持する変数
        formatted_contract_start_date = contract_start_date.strftime('%Y/%m/%d')
        
        holiday_periods_str_list = [f"{s.strftime('%Y/%m/%d')}〜{e.strftime('%Y/%m/%d')}" for s, e in st.session_state.holiday_periods]
        formatted_holiday_periods = ", ".join(holiday_periods_str_list) if holiday_periods_str_list else "設定なし"
        
        # 契約残存期間の計算を実行
        calculated_min_cancel_date_contract = calculate_min_cancel_date_contract_logic(contract_start_date, st.session_state.holiday_periods)
        calculated_min_cancel_date_declared = calculate_min_cancel_date_declared_logic(cancel_year, cancel_month, st.session_state.holiday_periods)
        
        # 残存期間と請求金額の計算
        remaining_months_rough = 0
        payment_plan_amount = 0
        
        if calculated_min_cancel_date_declared:
            today_date = datetime.today().date()
            # 解約希望日から現在までの月数を計算
            # 月の途中の場合は、日割り計算も検討可能だが、ここでは月単位で計算
            if calculated_min_cancel_date_declared >= today_date:
                remaining_months_rough = (calculated_min_cancel_date_declared.year - today_date.year) * 12 + \
                                         calculated_min_cancel_date_declared.month - today_date.month
                # 日付まで考慮するなら、さらに調整が必要 (例: 15日未満なら切り捨て、以上なら繰り上げなど)
                if calculated_min_cancel_date_declared.day < today_date.day:
                    remaining_months_rough -= 1
                if remaining_months_rough < 0:
                    remaining_months_rough = 0
            else:
                remaining_months_rough = 0 # 既に解約希望日が過去の場合
            
            payment_plan_amount = billing_unit_price * remaining_months_rough
            
        st.markdown(f"◆ Camel契約開始日：**{formatted_contract_start_date}**")
        st.markdown(f"◆ 休業期間：**{formatted_holiday_periods}**")
        st.markdown(f"◆ 最短解約日（契約期間）：**{calculated_min_cancel_date_contract.strftime('%Y/%m/%d') if calculated_min_cancel_date_contract else '計算不可'}**")
        st.markdown(f"◆ 最短解約日（申告日）：**{calculated_min_cancel_date_declared.strftime('%Y/%m/%d') if calculated_min_cancel_date_declared else '計算不可'}**")
        st.markdown(f"◆ 支払い状況：**{unpaid_amount:,.0f}円** （**{payment_status_text}**）")
        st.markdown(f"◆ 支払計画：**{payment_plan_amount:,.0f}円** （残存**{remaining_months_rough}ヶ月**）")
else:
    st.info("「全ての計算を実行」ボタンを押すと、結果が表示されます。")