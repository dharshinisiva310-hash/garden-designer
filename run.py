from transformers import AutoModelForCausalLM, AutoTokenizer

MODEL_PATH = r"D:\models\Qwen2.5-1.5B-Instruct"

print("Loading model... Please wait.")

tokenizer = AutoTokenizer.from_pretrained(
    MODEL_PATH,
    trust_remote_code=True
)

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

Examples:
- If asked about flowers, recommend suitable flowers and care tips.
- If asked about vegetables, suggest growing methods and maintenance.
- If asked about plant diseases, explain possible causes and remedies.
- If asked about garden design, suggest layouts and plant combinations.
"""
messages = [
    {"role": "system", "content": SYSTEM_PROMPT}
]

print("\nAI Gardening Assistant Ready!")
print("Type 'exit' to quit.\n")

while True:
    user_input = input("You: ")
    
    if user_input.lower() in ["exit", "quit"]:
        break
    
    messages.append({"role": "user", "content": user_input})
    
    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )
    
    inputs = tokenizer(text, return_tensors="pt").to(model.device)
    
    outputs = model.generate(
        **inputs,
        max_new_tokens=300,
        temperature=1.2,
        do_sample=True,
        pad_token_id=tokenizer.eos_token_id
    )
    
    response = tokenizer.decode(
        outputs[0][inputs["input_ids"].shape[1]:],
        skip_special_tokens=True
    )
    
    messages.append({"role": "assistant", "content": response})
    
    print("\nBot:", response)
    print("-" * 60)