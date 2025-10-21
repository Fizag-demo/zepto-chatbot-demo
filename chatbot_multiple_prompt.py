from transformers import pipeline
generator= pipeline("text2text-generation", model="google/flan-t5-base")
prompts=[
"what is zepto?",
"what all i can order from zepto?",
"can i order fruits"]

responses= generator(prompts)
for i, res in enumerate(responses):
    print(f"Prompt {i+1}: {prompts[i]}")
    print(f"Response: {res['generated_text']}\n")

