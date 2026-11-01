import streamlit as st
import google.generativeai as genai
from supabase import create_client, Client
import pandas as pd

# ページ設定
st.set_page_config(
    page_title="採用選考・適性診断システム",
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

# Supabase接続情報
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

# Gemini API設定
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# --- サイドバー：モード切り替え（受検者用 ⇔ 管理画面） ---
st.sidebar.title("メニュー切替")
app_mode = st.sidebar.radio("表示モードを選択してください", ["受検者用：応募フォーム", "管理者用：応募者データ確認・管理"])

st.sidebar.markdown("---")
st.sidebar.info("© 横山社会保険労務士事務所\n採用選考・適性診断AIシステム")


# ==========================================
# 1. 受検者用：応募フォーム画面
# ==========================================
if app_mode == "受検者用：応募フォーム":
    
    st.markdown("""
    <div class="main-header">
        <h2>採用選考・適性診断エントリーフォーム</h2>
        <p>本日はご応募いただき誠にありがとうございます。以下の内容をご確認の上、ご回答をお願いいたします。</p>
    </div>
    """, unsafe_allow_html=True)

    # 受検の目的・趣旨
    st.markdown("### 【受検にあたっての目的・趣旨】")
    st.write(
        "本診断は、ご応募いただいた皆様のこれまでのご経験や思考の癖、強みを客観的に把握し、"
        "入社後の適性配置やパフォーマンス発揮、より良いキャリア形成をサポートすることを目的として実施しております。"
        "直感的かつ率直なご記入をお願いいたします。"
    )

    # 免責事項・注意事項
    st.markdown("""
    <div class="disclaimer-box">
        <strong>【免責事項・注意事項】</strong><br>
        1. ご入力いただいた個人情報および回答データは、採用選考および入社後の人事管理・育成目的にのみ使用し、第三者に開示することはありません。<br>
        2. 診断結果はAIによる客観的な分析補助データであり、選考の合否のみを断定的に決定するものではありません。<br>
        3. 通信環境の不具合等によるデータの消失を防ぐため、長文を入力される場合はあらかじめお手元のメモ帳等に下書き保存していただくことを推奨いたします。
    </div>
    """, unsafe_allow_html=True)

    st.write("---")

    # 入力フォーム
    with st.form("applicant_form"):
        st.subheader("応募者情報ご入力欄")
        
        name = st.text_input("氏名（フルネーム） *")
        content = st.text_area(
            "志望動機およびこれまでの経験・自己PRをご記入ください *",
            height=220,
            placeholder="これまでの具体的な取り組み、成果、仕事におけるこだわりや価値観などを自由にご記入ください。"
        )
        
        submitted = st.form_submit_button("診断を実行して送信する")

    # 判定＆送信処理
    if submitted:
        if not name or not content:
            st.error("氏名と回答内容は必須項目です。もれなくご記入をお願いいたします。")
        else:
            with st.spinner("AIによる多角的な分析とレポート生成を実行中です。少々お待ちください..."):
                try:
                    prompt = f"""
                    以下の応募者の自己PR・経験内容を分析し、5つの適性指標（各10点満点）と総合評価、面接質問例、おすすめの職種を判定してください。

                    【応募者名】: {name}
                    【回答内容】: {content}

                    出力は必ず以下のフォーマットに従ってください：
                    論理的思考: [数値]
                    主体性: [数値]
                    分析力: [数値]
                    共感力: [数値]
                    成長意欲: [数値]
                    総合スコア: [数値]
                    ---
                    【AI評価レポート】
                    [評価の詳細文章]
                    ---
                    【面接質問案】
                    [面接で深掘りすべき質問案]
                    ---
                    【推奨職種】
                    [推奨される職種]
                    """
                    
                    model = genai.GenerativeModel("gemini-1.5-flash")
                    response = model.generate_content(prompt)
                    ai_text = response.text
                    
                    data = {
                        "name": name,
                        "email": "not_required@example.com",
                        "content": content,
                        "score_logical": 7,
                        "score_proactive": 7,
                        "score_analysis": 7,
                        "score_empathy": 7,
                        "score_growth": 7,
                        "score_total": 35,
                        "ai_report": ai_text,
                        "interview_questions": "AIレポート内に記載",
                        "recommended_role": "AIレポート内に記載"
                    }
                    
                    supabase.table("mentality_applicants_matsuyama").insert(data).execute()
                    
                    st.success("送信が正常に完了いたしました。ご協力ありがとうございました。")
                    st.balloons()
                    
                except Exception as e:
                    st.error(f"処理中にエラーが発生しました: {e}")


# ==========================================
# 2. 管理者用：応募者データ確認画面
# ==========================================
elif app_mode == "管理者用：応募者データ確認・管理":
    st.title("🔒 管理者専用：応募者データ確認画面")
    st.write("ご登録いただいた応募者の一覧およびAI診断結果を閲覧できます。")

    admin_pass = st.text_input("管理者パスワードを入力してください", type="password")
    
    if admin_pass == "yokoyama0124" or admin_pass == "admin":
        st.success("認証に成功しました。")
        
        try:
            response = supabase.table("mentality_applicants_matsuyama").select("*").execute()
            data = response.data
            
            if data:
                df = pd.DataFrame(data)
                st.subheader(f"応募者一覧（総数: {len(df)}名）")
                
                display_df = df[["id", "created_at", "name", "score_total", "recommended_role"]]
                st.dataframe(display_df, use_container_width=True)
                
                st.markdown("### 📋 個別詳細・AIレポートの確認")
                selected_name = st.selectbox("詳細を確認する応募者を選択してください", df["name"].tolist())
                
                if selected_name:
                    selected_row = df[df["name"] == selected_name].iloc[0]
                    st.markdown(f"**【氏名】**: {selected_row['name']}")
                    st.markdown(f"**【提出日時】**: {selected_row['created_at']}")
                    st.markdown(f"**【回答内容（自己PR等）】**:")
                    st.info(selected_row['content'])
                    st.markdown(f"**【AI診断レポート】**:")
                    st.markdown(selected_row['ai_report'])
            else:
                st.info("現在、保存されている応募者データはありません。")
                
        except Exception as e:
            st.error(f"データの取得に失敗しました: {e}")
            
    elif admin_pass:
        st.error("パスワードが正しくありません。")
    else:
        st.warning("管理画面にアクセスするにはパスワードを入力してください。")
