import json
import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

GEMINI_URL = 'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent'

VALID_CATEGORIES = ['Technical', 'Billing', 'General', 'Account Related']
VALID_PRIORITIES = ['Low', 'Medium', 'High']


class AIServiceError(Exception):
    pass


def build_prompt(subject, description):
    return f"""You are a customer support assistant. Analyse the customer query below.

Return ONLY a JSON object with these keys:
- "category": one of {VALID_CATEGORIES}
- "priority": one of {VALID_PRIORITIES}
- "suggested_response": a short, polite reply to the customer (1 to 2 sentences)

Priority rules:
- High: money lost, charged twice, cannot login, service down, security issue
- Medium: something is not working properly but there is a workaround
- Low: general questions, feedback, feature requests

Subject: {subject}
Query: {description}
"""


def call_gemini(prompt):
    if not settings.GEMINI_API_KEY:
        raise AIServiceError('GEMINI_API_KEY is not set')

    url = GEMINI_URL.format(model=settings.GEMINI_MODEL)
    headers = {
        'Content-Type': 'application/json',
        'x-goog-api-key': settings.GEMINI_API_KEY,
    }
    body = {
        'contents': [{'parts': [{'text': prompt}]}],
        'generationConfig': {
            'temperature': 0.2,
            'responseMimeType': 'application/json',
        },
    }

    try:
        response = requests.post(url, headers=headers, json=body, timeout=settings.GEMINI_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        return data['candidates'][0]['content']['parts'][0]['text']
    except requests.exceptions.Timeout:
        raise AIServiceError('Gemini request timed out')
    except requests.exceptions.RequestException as e:
        raise AIServiceError(f'Gemini request failed: {e}')
    except (KeyError, IndexError, ValueError):
        raise AIServiceError('Unexpected response format from Gemini')


def parse_ai_response(text):
    # sometimes the model wraps json in ```json ... ``` so remove that
    text = text.strip()
    if text.startswith('```'):
        text = text.strip('`')
        text = text.replace('json', '', 1).strip()

    try:
        result = json.loads(text)
    except json.JSONDecodeError:
        raise AIServiceError('AI did not return valid JSON')

    category = str(result.get('category', '')).strip()
    priority = str(result.get('priority', '')).strip()
    reply = str(result.get('suggested_response', '')).strip()

    # match ignoring case, in case model returns "billing" instead of "Billing"
    category = next((c for c in VALID_CATEGORIES if c.lower() == category.lower()), 'General')
    priority = next((p for p in VALID_PRIORITIES if p.lower() == priority.lower()), 'Medium')

    if not reply:
        reply = 'Thank you for contacting us. Our support team will review your query and get back to you soon.'

    return {
        'category': category,
        'priority': priority,
        'suggested_response': reply,
    }


# ---------- fallback (used when Gemini is not available) ----------

CATEGORY_KEYWORDS = {
    'Billing': ['payment', 'paid', 'refund', 'invoice', 'charged', 'deducted', 'bill', 'subscription', 'price'],
    'Account Related': ['account', 'login', 'log in', 'password', 'sign in', 'username', 'profile', 'locked'],
    'Technical': ['error', 'bug', 'crash', 'not working', 'issue', 'slow', 'install', 'app', 'website', 'server'],
}

HIGH_PRIORITY_WORDS = ['urgent', 'immediately', 'twice', 'deducted', 'not activated', 'cannot', "can't",
                       'hacked', 'down', 'asap', 'refund']
LOW_PRIORITY_WORDS = ['suggestion', 'feedback', 'how to', 'information', 'question', 'wondering']

FALLBACK_RESPONSES = {
    'Billing': 'We apologise for the inconvenience. Our billing team will check your payment details and get back to you shortly.',
    'Account Related': 'Sorry for the trouble with your account. Our team will look into it and help you regain access as soon as possible.',
    'Technical': 'Thanks for reporting this issue. Our technical team will investigate and update you soon.',
    'General': 'Thank you for reaching out. Our support team will review your query and respond shortly.',
}


def fallback_analysis(subject, description):
    text = f'{subject} {description}'.lower()

    category = 'General'
    for cat, words in CATEGORY_KEYWORDS.items():
        if any(word in text for word in words):
            category = cat
            break

    if any(word in text for word in HIGH_PRIORITY_WORDS):
        priority = 'High'
    elif any(word in text for word in LOW_PRIORITY_WORDS):
        priority = 'Low'
    else:
        priority = 'Medium'

    return {
        'category': category,
        'priority': priority,
        'suggested_response': FALLBACK_RESPONSES[category],
    }


def analyse_query(subject, description):
    """Try Gemini first, if anything goes wrong use the keyword based fallback."""
    try:
        text = call_gemini(build_prompt(subject, description))
        result = parse_ai_response(text)
        result['source'] = 'gemini'
    except AIServiceError as e:
        logger.warning('AI analysis failed, using fallback. Reason: %s', e)
        result = fallback_analysis(subject, description)
        result['source'] = 'fallback'
    return result
