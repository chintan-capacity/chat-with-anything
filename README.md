# Chat with Anything

Have a conversation about any content on the web. Simply paste a URL and start asking questions.

## What You Can Chat With

- YouTube videos
- News articles
- Blog posts
- Documentation
- Wikipedia articles
- Any public webpage

## Getting Started

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set your API key:

**Mac/Linux:**
```bash
export GEMINI_API_KEY="your_api_key_here"
```

**Windows (Command Prompt):**
```bash
set GEMINI_API_KEY=your_api_key_here
```

**Windows (PowerShell):**
```bash
$env:GEMINI_API_KEY="your_api_key_here"
```

3. Run the app:
```bash
streamlit run app.py
```

4. Open your browser and paste any URL

5. Start chatting!

## Features

✨ Works with any public URL
💬 Natural conversation interface
🔄 Remembers conversation context
📺 Video preview for YouTube
🎯 Simple and intuitive

## Notes

- YouTube videos must have captions/transcripts available
- Web pages must be publicly accessible
- If you don't set the environment variable, you can enter your API key in the app
