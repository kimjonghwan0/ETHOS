import streamlit as st
import os
import json
from dotenv import load_dotenv
import google.generativeai as genai

# 1. 환경 변수 및 설정 로드
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

# 2. 세션 상태 초기화
def init_session_state():
    if "user" not in st.session_state:
        st.session_state.user = None
    if "current_stage" not in st.session_state:
        st.session_state.current_stage = 0
    if "api_key" not in st.session_state:
        st.session_state.api_key = API_KEY
    if "simulator_started" not in st.session_state:
        st.session_state.simulator_started = False
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "sim_stage" not in st.session_state:
        st.session_state.sim_stage = "T1"
    if "same_turn_count" not in st.session_state:
        st.session_state.same_turn_count = 0
    if "hint_auto_shown" not in st.session_state:
        st.session_state.hint_auto_shown = set()
    if "sim_status" not in st.session_state:
        st.session_state.sim_status = "ongoing"

init_session_state()

# 3. 데이터 및 프롬프트 설정 (보내주신 데이터 포함)
SCENARIO_PUBLIC = {
    "scenario_01": {
        "title": "정보보호",
        "persona_name": "이현도",
        "persona_role": "사수 (시니어 개발자 3년차)",
        "situation": "오전 10시 40분. 20분 뒤면 팀 전체 주간 회의가 잡혀 있다...",
        "initial_message": "야, 나 어젯밤에 이 기능 겨우 끝냈다. ChatGPT한테 우리 DB 스키마랑 API 키 통째로 붙여넣고 코드 짜달라고 했어. 어차피 ChatGPT는 입력 데이터 학습 안 한다고 약관에 나와 있잖아. 너도 막히면 이렇게 써봐, 엄청 빠르거든. 오늘 회의 때 데모 보여줄 수 있을 것 같아 👍",
        "persona_intro": "어젯밤 야근으로 기능을 끝낸 걸 내심 뿌듯해하는 사수...",
        "persona_attitude": '"그 정도 판단은 내가 할 수 있어. 약관도 읽어봤고, 3년 동안 이렇게 해왔는데 문제 생긴 적 없잖아."',
        "hint_main": "논리보다 먼저 어젯밤 야근을 알아줘 보세요.",
        "hints": {
            "T1": "대형 IT 기업 중에 사내 AI 도구 사용을 전면 금지한 곳이 있어요. 왜 그런 결정을 내렸을지 이현도에게 물어보세요.",
            "T2": "만약 당신이 이 API 키를 손에 넣은 외부인이라면 무엇을 할 수 있을까요?",
            "T3": "API 키 유출이 이현도 본인에게 어떤 결과를 가져올 수 있는지 짚어보세요."
        }
    }
    # (나머지 시나리오 02~05는 지면상 생략했으나, 필요시 동일 구조로 추가 가능합니다)
}

SCENARIO_SYSTEM_PROMPTS = {
    "scenario_01": """[페르소나: 이현도 — 시니어 개발자 3년차, 사수]
성격: 야근 인정에 약함, 실력 자부심 강함, 논리적 근거에 결국 수긍함.
... (보내주신 세부 프롬프트 내용)
"""
}

COMMON_SYSTEM = """
[공통 운영 원칙]
- 응답은 반드시 아래 JSON 형식으로만 출력하세요:
{"stage": "T1~T5", "message": "대화 내용", "result": "success/fail/null"}
"""

# 4. API 호출 함수
def call_gemini(scenario_id, messages):
    genai.configure(api_key=st.session_state.api_key)
    system_prompt = COMMON_SYSTEM + "\n\n" + SCENARIO_SYSTEM_PROMPTS.get(scenario_id, "")
    
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        system_instruction=system_prompt,
        generation_config={"response_mime_type": "application/json"}
    )
    
    history = [{"role": "user" if m["role"] == "user" else "model", "parts": [m["content"]]} for m in messages[:-1]]
    chat = model.start_chat(history=history)
    response = chat.send_message(messages[-1]["content"])
    
    return json.loads(response.text)

# 5. UI 렌더링
st.set_page_config(page_title="ETHOS - AI 윤리 교육", layout="wide")

# CSS 로드
st.markdown("""<style>
    .stApp { background-color: #f8fafc; }
    .chat-box { padding: 20px; border-radius: 10px; border: 1px solid #e0e0e0; background: white; }
</style>""", unsafe_allow_html=True)

# 메인 화면 제어
if st.session_state.user is None:
    st.title("🛡️ AI 윤리 교육 시스템 ETHOS")
    with st.form("login"):
        name = st.text_input("이름")
        if st.form_submit_button("시작하기"):
            st.session_state.user = name
            st.rerun()
else:
    # 사이드바
    st.sidebar.title(f"반가워요, {st.session_state.user}님")
    if st.sidebar.button("로그아웃"):
        st.session_state.clear()
        st.rerun()

    # 시뮬레이터 로직
    if not st.session_state.simulator_started:
        st.subheader("학습할 시나리오를 선택하세요")
        sel = st.selectbox("시나리오 목록", list(SCENARIO_PUBLIC.keys()))
        pub = SCENARIO_PUBLIC[sel]
        st.info(f"**상황:** {pub['situation']}")
        if st.button("시뮬레이션 시작"):
            st.session_state.scenario_id = sel
            st.session_state.simulator_started = True
            st.session_state.messages = [{"role": "assistant", "content": pub["initial_message"]}]
            st.rerun()
    else:
        # 채팅창 구성
        sid = st.session_state.scenario_id
        pub = SCENARIO_PUBLIC[sid]
        
        st.title(f"💬 {pub['title']} 세션")
        st.write(f"현재 단계: **{st.session_state.sim_stage}**")

        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

        if st.session_state.sim_status == "ongoing":
            if prompt := st.chat_input("메시지를 입력하세요"):
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"): st.write(prompt)
                
                with st.spinner("생각 중..."):
                    res = call_gemini(sid, st.session_state.messages)
                    st.session_state.sim_stage = res.get("stage", st.session_state.sim_stage)
                    st.session_state.messages.append({"role": "assistant", "content": res["message"]})
                    
                    if res.get("result") == "success":
                        st.balloons()
                        st.success("설득에 성공했습니다!")
                        st.session_state.sim_status = "end"
                    st.rerun()