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
You are an AI Recommendation Assistant.
Give simple, beginner-friendly recommendations.
"""

# Chat history starts here
messages = [
    {
        "role": "system",
        "content": SYSTEM_PROMPT
    }
]

print("Chatbot Ready!")

while True:

    user_input = input("You: ")

    if user_input.lower() == "exit":
        break

    # Add user's message
    messages.append(
        {
            "role": "user",
            "content": user_input
        }
    )

    # Convert conversation into model input
    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )

    inputs = tokenizer(text, return_tensors="pt").to(model.device)

    outputs = model.generate(
        **inputs,
        max_new_tokens=300,
        temperature=0.7,
        do_sample=True,
        pad_token_id=tokenizer.eos_token_id
    )

    response = tokenizer.decode(
        outputs[0][inputs["input_ids"].shape[1]:],
        skip_special_tokens=True
    )

    # Save assistant response
    messages.append(
        {
            "role": "assistant",
            "content": response
        }
    )

    print("\nBot:", response)
    print("-" * 50)