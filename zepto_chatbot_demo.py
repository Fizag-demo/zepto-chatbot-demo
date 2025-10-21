from transformers import pipeline

# Load the model pipeline (text-to-text generation)
# This downloads the model if not cached (~250MB, one-time)
model = pipeline("text2text-generation", model="google/flan-t5-base")

# Your prompt
prompt = "Hello! Can you answer simple customer questions about Zepto orders?"

# Generate response
# Adjust parameters as needed (e.g., max_length for output length)
response = model(prompt, max_length=100, num_return_sequences=1, temperature=0.7)

# Print the generated text
print(response[0]["generated_text"])