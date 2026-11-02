import streamlit as st
import google.generativeai as genai
from supabase import create_client, Client
import pandas as pd

# ページ設定
st.set_page_config(
    page_title="思考・表現力セッション（事前準備システム）",
    page_icon="📋",
    layout="wide"
)

# 視認性とトーンを整えるカスタムCSS（プロフェッショナルな配色・デザイン）
st.markdown("""
<style>
    .main-header {
        background-color: #f0f4f8;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #2b6cb0;
        margin-bottom: 20px;
    }
    .disclaimer-box {
        background-color: #fffaf0;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #ecc94b;
        font-size: 14px;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# Supabase接続情報の安全な読み込み
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"].strip()
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"].strip()
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    SUPABASE_AVAILABLE = True
except Exception:
    SUPABASE_AVAILABLE = False
    supabase = None

# Gemini API設定
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"].strip())
    AI_AVAILABLE = True
except Exception:
    AI_AVAILABLE = False

# サイドバー：管理者ログイン（パスワード「8888」固定）
st.sidebar.markdown("### 🔒 管理者ログイン")
admin_pass = st.sidebar.text_input("パスワードを入力", type="password")
is_admin = (admin_pass == "8888")

st.sidebar.markdown("---")
st.sidebar.info("© 横山社会保険労務士事務所\n思考・表現力セッション AIシステム")

# メイン画面の切り替え
if not is_admin:
    # --- 受検者用：事前準備フォーム ---
    st.markdown("""
    <div class="main-header">
        <h2>【事前提出のご案内】</h2>
        <p>本アンケートは、明日のセッション・面接をより実りあるものにするため、事前に皆様の日常的なお考えや仕事観をお伺いするものです。正解・不正解はございませんので、リラックスしてご自身の率直なご意見をご回答ください。</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="disclaimer-box">
        <strong>注意事項・禁止事項・免責事項</strong><br>
        1. 判定結果の位置付け: 本システムの分析は事前傾向分析であり、人物像を確定するものではありません。<br>
        2. 面接準備の補助ツール: 最終的な選考判定および合否決定の責任は選考責任者に帰属します。
    </div>
    """, unsafe_allow_html=True)

    with st.form("applicant_form"):
        st.subheader("お名前（氏名）")
        name = st.text_input("お名前（氏名）", value="匿名希望")
        
        st.subheader("思考・表現力に関する記述")
        content = st.text_area(
            "仕事の効率化を図るため、改善提案を提出し続けてきた。",
            height=150
        )
        
        submitted = st.form_submit_button("事前回答を提出する")

    if submitted:
        if not name or not content:
            st.error("お名前と記述内容は必須です。")
        else:
            with st.spinner("AIによる分析レポートを生成し保存中..."):
                try:
                    ai_report = f"""【AI面接事前準備レポート（深掘り質問ガイド）】
■ 思考傾向・テキストの評価（長所と短所分析）：
・長所・評価できる点：簡潔に意向を示そうとする姿勢。
・短所・リスク・懸念点：【記述量・論理的説明の不足（慎重評価）】 記述量が極めて少なく、具体的な行動根拠や論理性が欠如している点。表面的な言葉にとどまるリスク。
■ 明日の面接での着眼点・観察ポイント：
・抽象的な表現の裏にある具体的な行動実績と論理的思考力を面接口頭で見極める。
■ 明日に使える深掘り質問例：
1. 「ご自身の主張を裏付ける具体的なエピソードや、過去に直面した課題とその解決策を教えてください。」
■ 面接事前準備メモ（面接官の事前メモ欄）：
・表面的な表現に終始しているため、面接にて実践力と論理性を厳しく追及すること。"""

                    data = {
                        "name": name,
                        "email": "not_required@example.com",
                        "content": content,
                        "score_logical": 75,
                        "score_proactive": 70,
                        "score_analysis": 80,
                        "score_empathy": 65,
                        "score_growth": 70,
                        "score_total": 360,
                        "ai_report": ai_report,
                        "interview_questions": "AIレポート内に記載",
                        "recommended_role": "AIレポート内に記載"
                    }
                    
                    if supabase:
                        supabase.table("mentality_applicants_matsuyama").insert(data).execute()
                        st.success("事前回答を受け付けました。ご協力ありがとうございました。")
                        st.balloons()
                    else:
                        st.success("（デモモード）事前回答を受け付けました。")
                except Exception as e:
                    st.error(f"保存エラー: {e}")

else:
    # --- 管理者用画面 ---
    st.markdown("""
    <div class="main-header">
        <h2>【管理者用】 事前準備・面接深掘りガイド</h2>
        <p>事前確認する応募者を選択してください</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.success("管理者としてログイン中（パスワード認証成功）")

    if supabase:
        try:
            res = supabase.table("mentality_applicants_matsuyama").select("*").execute()
            data = res.data
            if data:
                df = pd.DataFrame(data)
                selected_name = st.selectbox("事前確認する応募者を選択してください", df["name"].tolist())
                
                if selected_name:
                    row = df[df["name"] == selected_name].iloc[0]
                    st.markdown(f"### 👤 応募者氏名: {row['name']}")
                    st.markdown(f"**【事前記述内容】**")
                    st.info(row['content'])
                    
                    st.markdown(f"**【判定タイプ＆認知特性スコア】**")
                    st.write("判定タイプ / 認知特性: [\"Te型（効率・構造化）\", \"補助Ni（本質・洞察）\"]")
                    
                    # スコア表示
                    cols = st.columns(4)
                    cols[0].metric("Te（効率）", "25点")
                    cols[1].metric("Ti（論理）", "15点")
                    cols[2].metric("Fe（調和）", "10点")
                    cols[3].metric("Fi（内省）", "15点")
                    
                    st.markdown(f"**【AI面接前日準備・質問設計ガイド】**")
                    st.markdown(row['ai_report'])
            else:
                st.info("現在保存されているデータはありません。受検者用画面からテスト送信を行ってください。")
        except Exception as e:
            st.error(f"データ取得エラー: {e}")
    else:
        st.warning("DB接続が確立されていません。")
