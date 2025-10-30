import streamlit as st
import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi
import re
import os
import requests
from bs4 import BeautifulSoup
from typing import Optional, Tuple
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Page configuration
st.set_page_config(
    page_title="Chat with URL",
    page_icon="🔗",
    layout="wide"
)

def is_youtube_url(url: str) -> bool:
    """Check if URL is a YouTube URL"""
    youtube_patterns = [
        r'(youtube\.com\/watch\?v=)',
        r'(youtu\.be\/)',
        r'(youtube\.com\/embed\/)',
        r'(youtube\.com\/v\/)'
    ]
    return any(re.search(pattern, url) for pattern in youtube_patterns)

def extract_video_id(url: str) -> Optional[str]:
    """Extract video ID from YouTube URL"""
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&\n?#]+)',
        r'youtube\.com\/embed\/([^&\n?#]+)',
        r'youtube\.com\/v\/([^&\n?#]+)'
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def get_youtube_transcript_v3(video_id: str, api_key: str) -> str:
    """Fetch transcript using YouTube Data API v3"""
    try:
        youtube = build('youtube', 'v3', developerKey=api_key)

        # Get caption tracks for the video
        captions_response = youtube.captions().list(
            part='snippet',
            videoId=video_id
        ).execute()

        if not captions_response.get('items'):
            raise Exception("No captions available for this video")

        # Find English caption track (or first available)
        caption_id = None
        for item in captions_response['items']:
            if item['snippet']['language'] == 'en':
                caption_id = item['id']
                break

        if not caption_id and captions_response['items']:
            caption_id = captions_response['items'][0]['id']

        if not caption_id:
            raise Exception("No suitable caption track found")

        # Download the caption
        caption_response = youtube.captions().download(
            id=caption_id,
            tfmt='srt'
        ).execute()

        # Parse SRT format to extract text
        import re
        text_lines = []
        for block in caption_response.decode('utf-8').split('\n\n'):
            lines = block.strip().split('\n')
            if len(lines) >= 3:
                # Skip timestamp and number, get the text
                text_lines.append(' '.join(lines[2:]))

        return ' '.join(text_lines)

    except HttpError as e:
        if e.resp.status == 403:
            raise Exception(f"YouTube API quota exceeded or captions are disabled for this video")
        raise Exception(f"YouTube API error: {str(e)}")
    except Exception as e:
        raise Exception(f"Error fetching transcript via YouTube API: {str(e)}")

def get_youtube_transcript(video_id: str, gemini_api_key: str = "") -> str:
    """Fetch transcript for a YouTube video with fallback to YouTube Data API v3"""

    # Try youtube-transcript-api first (free, but may be blocked on cloud)
    try:
        ytt_api = YouTubeTranscriptApi()
        fetched_transcript = ytt_api.fetch(video_id)
        transcript = " ".join([snippet.text for snippet in fetched_transcript])
        return transcript
    except Exception as transcript_api_error:
        # If transcript API fails, try YouTube Data API v3
        if gemini_api_key:
            try:
                return get_youtube_transcript_v3(video_id, gemini_api_key)
            except Exception as v3_error:
                raise Exception(
                    f"Failed to fetch transcript. "
                    f"youtube-transcript-api error: {str(transcript_api_error)}. "
                    f"YouTube Data API v3 error: {str(v3_error)}"
                )
        else:
            raise Exception(f"Error fetching transcript: {str(transcript_api_error)}")

def fetch_url_content(url: str) -> str:
    """Fetch content from any URL"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        # Try with SSL verification first, then without if it fails
        try:
            response = requests.get(url, headers=headers, timeout=30, verify=True)
        except requests.exceptions.SSLError:
            st.warning("SSL verification failed. Retrying without SSL verification...")
            response = requests.get(url, headers=headers, timeout=30, verify=False)

        response.raise_for_status()

        # Check if it's a PDF
        content_type = response.headers.get('content-type', '').lower()
        if 'application/pdf' in content_type or url.lower().endswith('.pdf'):
            raise Exception("PDF files are not yet supported. Please use the URL of the webpage containing the PDF, or try a different URL.")

        # Parse HTML content
        soup = BeautifulSoup(response.content, 'html.parser')

        # Remove script and style elements
        for script in soup(['script', 'style', 'nav', 'footer', 'header']):
            script.decompose()

        # Get text
        text = soup.get_text()

        # Clean up text
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)

        if not text or len(text.strip()) < 50:
            raise Exception("Unable to extract meaningful text from the URL. The page might be empty or dynamically loaded.")

        return text
    except Exception as e:
        raise Exception(f"Error fetching URL content: {str(e)}")

def get_content_from_url(url: str, api_key: str = "") -> Tuple[str, str]:
    """Get content from URL (YouTube or regular webpage)
    Returns: (content, content_type)"""
    if is_youtube_url(url):
        video_id = extract_video_id(url)
        if not video_id:
            raise Exception("Invalid YouTube URL")
        content = get_youtube_transcript(video_id, api_key)
        return content, "youtube"
    else:
        content = fetch_url_content(url)
        return content, "webpage"

def initialize_gemini(api_key: str):
    """Initialize Gemini API"""
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
    return model

# UI Layout
st.title("🔗 Chat with URL")
st.markdown("Chat with any URL using AI - powered by Gemini. Supports YouTube videos and web pages!")

# Get API key from environment variable
api_key = os.getenv("GEMINI_API_KEY", "")

# Sidebar for configuration
with st.sidebar:
    st.header("⚙️ Configuration")

    if api_key:
        st.success("✓ API Key loaded from environment")
    else:
        api_key = st.text_input("Gemini API Key", type="password", help="Get your API key from https://makersuite.google.com/app/apikey or set GEMINI_API_KEY environment variable")

    st.markdown("---")
    st.markdown("### How to use:")
    st.markdown("1. Set GEMINI_API_KEY env variable (or enter manually)")
    st.markdown("2. Paste any URL (YouTube video or webpage)")
    st.markdown("3. Click 'Load URL'")
    st.markdown("4. Start chatting!")

# Main area
url = st.text_input("Enter any URL", placeholder="https://www.youtube.com/watch?v=... or https://example.com/article")

if st.button("Load URL", type="primary"):
    if not api_key:
        st.error("Please enter your Gemini API key in the sidebar")
    elif not url:
        st.error("Please enter a URL")
    else:
        with st.spinner("Loading content from URL..."):
            try:
                # Get content from URL
                content, content_type = get_content_from_url(url, api_key)

                # Initialize Gemini chat session
                model = initialize_gemini(api_key)

                # Create initial context based on content type
                if content_type == "youtube":
                    system_instruction = f"""You are an AI assistant helping users understand and discuss a YouTube video.

Here is the full transcript of the video:

{content}

Based on this transcript, please answer the user's questions. Be helpful, accurate, and reference specific parts of the transcript when relevant. Maintain context from previous questions in our conversation."""
                else:
                    system_instruction = f"""You are an AI assistant helping users understand and discuss content from a webpage.

Here is the full content from the webpage:

{content}

Based on this content, please answer the user's questions. Be helpful, accurate, and reference specific parts when relevant. Maintain context from previous questions in our conversation."""

                # Start chat session with context
                chat = model.start_chat(history=[])

                # Send initial system context (as a hidden message)
                initial_response = chat.send_message(system_instruction)

                # Store in session state
                st.session_state.content = content
                st.session_state.content_type = content_type
                st.session_state.url = url
                st.session_state.api_key = api_key
                st.session_state.messages = []
                st.session_state.chat = chat

                if content_type == "youtube":
                    st.success("YouTube video loaded successfully! You can now chat about it.")
                else:
                    st.success("Webpage loaded successfully! You can now chat about it.")
                st.rerun()

            except Exception as e:
                st.error(f"Error: {str(e)}")

# Display content and chat interface if content is loaded
if 'content' in st.session_state:
    st.markdown("---")

    col1, col2 = st.columns([1, 2])

    with col1:
        if st.session_state.content_type == "youtube":
            st.subheader("Video Preview")
            st.video(st.session_state.url)
        else:
            st.subheader("URL Info")
            st.text_input("Loaded URL", st.session_state.url, disabled=True)

        with st.expander("View Content"):
            content_label = "Transcript" if st.session_state.content_type == "youtube" else "Page Content"
            st.text_area(content_label, st.session_state.content, height=300, disabled=True)

    with col2:
        col_title, col_clear = st.columns([4, 1])
        with col_title:
            chat_title = "Chat about the video" if st.session_state.content_type == "youtube" else "Chat about the content"
            st.subheader(chat_title)
        with col_clear:
            if st.button("Clear Chat", type="secondary"):
                # Reinitialize chat session
                model = initialize_gemini(st.session_state.api_key)

                if st.session_state.content_type == "youtube":
                    system_instruction = f"""You are an AI assistant helping users understand and discuss a YouTube video.

Here is the full transcript of the video:

{st.session_state.content}

Based on this transcript, please answer the user's questions. Be helpful, accurate, and reference specific parts of the transcript when relevant. Maintain context from previous questions in our conversation."""
                else:
                    system_instruction = f"""You are an AI assistant helping users understand and discuss content from a webpage.

Here is the full content from the webpage:

{st.session_state.content}

Based on this content, please answer the user's questions. Be helpful, accurate, and reference specific parts when relevant. Maintain context from previous questions in our conversation."""

                chat = model.start_chat(history=[])
                initial_response = chat.send_message(system_instruction)

                st.session_state.chat = chat
                st.session_state.messages = []
                st.rerun()

        # Create a scrollable chat container with fixed height
        st.markdown("""
        <style>
        .chat-container {
            height: 500px;
            overflow-y: auto;
            padding: 10px;
            margin-bottom: 10px;
        }
        /* Make chat input stay at bottom */
        .stChatInput {
            position: sticky;
            bottom: 0;
            background: var(--background-color);
            padding-top: 1rem;
        }
        </style>
        """, unsafe_allow_html=True)

        # Display chat messages in scrollable container
        chat_container = st.container(height=500)
        with chat_container:
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

        # Chat input at bottom
        prompt_placeholder = "Ask anything about the video..." if st.session_state.content_type == "youtube" else "Ask anything about the content..."
        if prompt := st.chat_input(prompt_placeholder):
            # Add user message
            st.session_state.messages.append({"role": "user", "content": prompt})

            # Generate response
            try:
                # Use existing chat session to maintain context
                response = st.session_state.chat.send_message(prompt)
                assistant_message = response.text

                # Add assistant message
                st.session_state.messages.append({"role": "assistant", "content": assistant_message})

            except Exception as e:
                error_msg = f"Error generating response: {str(e)}"
                st.session_state.messages.append({"role": "assistant", "content": error_msg})

            # Rerun to update the chat display
            st.rerun()

else:
    st.info("👆 Enter any URL above to get started!")
