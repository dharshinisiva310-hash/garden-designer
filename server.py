import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from transformers import AutoModelForCausalLM, AutoTokenizer

MODEL_PATH = r"D:\models\Qwen2.5-1.5B-Instruct"

print("Loading model... Please wait.")
tokenizer = AutoTokenizer.from_pretrained(
    MODEL_PATH,
    trust_remote_code=True
)
#git status
model = AutoModelForCausalLM.from_pretrained(
    MODEL_PATH,
    torch_dtype="auto",
    device_map="auto",
    trust_remote_code=True
)

SYSTEM_PROMPT = """
You are an AI Gardening Assistant.

Your job is to help users with gardening, plant care, landscaping, and growing healthy plants.

Rules:
1. Recommend plants based on the user's environment and needs.
2. Provide simple and practical gardening advice.
3. Suggest watering schedules, sunlight requirements, and soil types.
4. Help diagnose common plant problems and suggest solutions.
5. Recommend suitable fertilizers and plant care tips.
6. Suggest seasonal gardening activities when relevant.
7. Return recommendations in a numbered list whenever possible.
8. Keep answers concise, beginner-friendly, and easy to follow.
9. If the user wants to grow a plant, explain the steps from planting to maintenance.
10. Always encourage sustainable and eco-friendly gardening practices.
"""

messages = [
    {
        "role": "system",
        "content": SYSTEM_PROMPT
    }
]

class ChatHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Default route to index.html
        path = self.path
        if path == "/" or path == "":
            path = "/index.html"
        
        # Prevent directory traversal
        clean_path = path.lstrip("/")
        # Extract path relative to this script
        base_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(base_dir, "static", clean_path)
        
        # Normalize paths and check containment under base_dir/static
        static_dir = os.path.join(base_dir, "static")
        real_file_path = os.path.realpath(file_path)
        real_static_dir = os.path.realpath(static_dir)
        
        if real_file_path.startswith(real_static_dir) and os.path.exists(real_file_path) and os.path.isfile(real_file_path):
            self.send_response(200)
            
            # Set correct Content-Type
            if real_file_path.endswith(".html"):
                self.send_header("Content-Type", "text/html; charset=utf-8")
            elif real_file_path.endswith(".css"):
                self.send_header("Content-Type", "text/css; charset=utf-8")
            elif real_file_path.endswith(".js"):
                self.send_header("Content-Type", "application/javascript; charset=utf-8")
            elif real_file_path.endswith(".png"):
                self.send_header("Content-Type", "image/png")
            elif real_file_path.endswith(".ico"):
                self.send_header("Content-Type", "image/x-icon")
            else:
                self.send_header("Content-Type", "application/octet-stream")
                
            self.end_headers()
            with open(real_file_path, "rb") as f:
                self.wfile.write(f.read())
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"File Not Found")
            
    def do_POST(self):
        global messages
        if self.path == "/api/chat":
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode('utf-8'))
                user_message = data.get("message", "")
                
                # Append user query
                messages.append({"role": "user", "content": user_message})
                
                # Format prompt
                text = tokenizer.apply_chat_template(
                    messages,
                    tokenize=False,
                    add_generation_prompt=True
                )
                
                inputs = tokenizer(text, return_tensors="pt").to(model.device)
                
                outputs = model.generate(
                    **inputs,
                    max_new_tokens=400,
                    temperature=0.7,
                    do_sample=True,
                    pad_token_id=tokenizer.eos_token_id
                )
                
                response = tokenizer.decode(
                    outputs[0][inputs["input_ids"].shape[1]:],
                    skip_special_tokens=True
                )
                
                # Append assistant response
                messages.append({"role": "assistant", "content": response})
                
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                
                response_data = {
                    "response": response,
                    "history": messages
                }
                self.wfile.write(json.dumps(response_data).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
                
        elif self.path == "/api/reset":
            messages = [
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                }
            ]
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "success", "message": "Conversation history reset."}).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

def run_server(port=8000):
    server_address = ('', port)
    httpd = HTTPServer(server_address, ChatHandler)
    print(f"Web UI Server running on http://localhost:{port}/")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server.")
        httpd.server_close()

if __name__ == "__main__":
    run_server()
