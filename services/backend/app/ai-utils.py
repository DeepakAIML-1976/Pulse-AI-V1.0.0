import random
import openai

# Optional: Use environment variable for model configuration
openai.api_key = "YOUR_OPENAI_API_KEY"

async def analyze_mood_text(text: str):
    """
    Very simple placeholder for emotion detection.
    In production, replace with a proper sentiment/emotion classifier.
    """
    if not text:
        return "neutral", 0.5

    text_lower = text.lower()
    if any(word in text_lower for word in ["happy", "joy", "grateful", "calm"]):
        return "calm", 0.9
    elif any(word in text_lower for word in ["sad", "tired", "depressed", "upset"]):
        return "sad", 0.9
    elif any(word in text_lower for word in ["angry", "frustrated", "annoyed"]):
        return "angry", 0.85
    elif any(word in text_lower for word in ["anxious", "nervous", "worried"]):
        return "anxious", 0.88
    else:
        return "neutral", 0.7


async def generate_empathy_response(emotion: str, text: str):
    """
    Generate a gentle, context-aware empathetic message.
    You can replace this with an LLM API call for richer responses.
    """
    templates = {
        "calm": "That’s wonderful to hear. Calmness helps restore balance — enjoy your peace 🌿",
        "sad": "I’m sorry you’re feeling down. Remember, it’s okay to take a moment for yourself 💙",
        "angry": "Anger can be tough — maybe a deep breath or short walk could help ease it 🌬️",
        "anxious": "Feeling anxious is natural sometimes. Let’s take a slow deep breath together 🌸",
        "neutral": "Thanks for sharing. Staying aware of your emotions helps you grow 🪴",
    }

    return templates.get(emotion, "I’m here for you — thank you for sharing how you feel 💫")
