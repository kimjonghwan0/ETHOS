import os
import urllib.request
import urllib.error
from http.server import SimpleHTTPRequestHandler, HTTPServer
from dotenv import load_dotenv
import webbrowser
import google.generativeai as genai
import json

# .env 파일 로드
load_dotenv()

# 환경변수에서 API 키 가져오기
API_KEY = os.getenv("GEMINI_API_KEY")

# Gemini 설정
if API_KEY:
    genai.configure(api_key=API_KEY)

class ProxyHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        # API 이외의 GET 요청은 기본 정적 파일 제공기능 사용
        # 기본 문서를 index_v2.html로 설정
        if self.path == '/':
            self.path = '/index.html'
        
        return super().do_GET()

    def do_POST(self):
        # /api/chat 경로로 POST 요청이 오면 Gemini로 처리
        if self.path == '/api/chat':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                request_data = json.loads(post_data)
                messages = request_data.get('messages', [])
                
                # 시스템 프롬프트 및 메시지 분리
                system_instruction = ""
                history = []
                
                for msg in messages:
                    if msg['role'] == 'system':
                        system_instruction = msg['content']
                    else:
                        role = "model" if msg['role'] == 'assistant' else "user"
                        history.append({"role": role, "parts": [msg['content']]})
                
                # 마지막 메시지는 send_message에 사용하기 위해 history에서 제거
                if history:
                    last_message = history.pop()
                    last_text = last_message['parts'][0]
                else:
                    last_text = ""

                # Gemini 모델 설정
                model = genai.GenerativeModel(
                    model_name="gemini-1.5-flash",
                    system_instruction=system_instruction if system_instruction else None,
                    generation_config={"response_mime_type": "application/json"}
                )
                
                # 채팅 시작 및 응답 생성
                chat = model.start_chat(history=history)
                response = chat.send_message(last_text)
                
                # OpenAI 형식의 응답으로 변환 (기존 HTML 호환성 유지)
                openai_response = {
                    "choices": [
                        {
                            "message": {
                                "role": "assistant",
                                "content": response.text
                            }
                        }
                    ]
                }
                
                res_body = json.dumps(openai_response).encode('utf-8')
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(res_body)
                
            except Exception as e:
                # 에러 발생 시 클라이언트(HTML)로 에러 전달
                print(f"❌ API 오류 발생: {str(e)}")
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "error": {
                        "message": f"Gemini API 호출 중 오류가 발생했습니다: {str(e)}"
                    }
                }).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == '__main__':
    if not API_KEY:
        print("❌ 오류: .env 파일에 GEMINI_API_KEY가 설정되어 있지 않습니다.")
        print("API 키를 설정하고 다시 실행해주세요.")
    else:
        # 고정 포트(예: 8080)로 서버 열기
        PORT = 8080
        server_address = ('', PORT)
        httpd = HTTPServer(server_address, ProxyHandler)
        
        print(f"✅ 로컬 서버가 시작되었습니다! API 키는 백엔드에 안전하게 보관됩니다.")
        print(f"웹 브라우저에서 아래 주소로 접속하세요:")
        print(f"👉 http://localhost:{PORT}/index.html")
        
        # 자동으로 브라우저 열기
        try:
            webbrowser.open(f"http://localhost:{PORT}/index.html")
        except:
            pass
            
        # 서버 무한 대기
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n서버를 종료합니다.")
            httpd.server_close()
