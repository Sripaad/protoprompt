import time
from groq import Groq

client = Groq()

# Non-streaming example
start_time = time.time()
completion = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[
        {
            "role": "user",
            "content": "Explain why fast inference is critical for reasoning models"
        }
    ]
)
response_text = completion.choices[0].message.content
elapsed = time.time() - start_time
num_tokens = len(response_text.split())
print("Non-streaming response:")
# print(response_text)
print(f"\nNon-streaming: {num_tokens} tokens in {elapsed:.2f} sec ({num_tokens/elapsed:.2f} tokens/sec)\n")

# Streaming example
print("Streaming response:")
stream_start = time.time()
stream = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[
        {
            "role": "user",
            "content": "Explain why fast inference is critical for reasoning models"
        }
    ],
    stream=True
)

streamed_tokens = 0
streamed_text = ""
for chunk in stream:
    content = chunk.choices[0].delta.content
    if content:
        print(content, end="", flush=True)
        streamed_text += content
        streamed_tokens += len(content.split())

stream_elapsed = time.time() - stream_start
print(f"\n\nStreaming: {streamed_tokens} tokens in {stream_elapsed:.2f} sec ({streamed_tokens/stream_elapsed:.2f} tokens/sec)")