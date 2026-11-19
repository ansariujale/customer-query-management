# AI Integration - Short Explanation

## Which AI model/API was used?

Google Gemini (`gemini-3.5-flash-lite`) through the Gemini REST API. I picked it because it has a free tier, it is fast, and it can return a JSON response directly, which makes the output easy to read in code. The model name is in `.env` so it can be changed without touching the code.

## How was it integrated with Django?

All AI code is in one file, `queries/ai_service.py`, so the views do not need to know anything about Gemini.

1. The user calls `POST /api/queries/{id}/analyze/`.
2. The view loads the query (only if it belongs to the logged in user) and calls `analyse_query(subject, description)`.
3. `build_prompt()` creates a prompt that lists the allowed categories and priorities and asks for JSON only.
4. `call_gemini()` sends the prompt with `requests.post()`. The API key is read from `settings.GEMINI_API_KEY`, which comes from the `.env` file. A timeout is set so the request cannot hang.
5. The result is saved on the query (category, priority, suggested_response, analysed_by, analysed_at) and returned in the response.

## How is the AI response processed and interpreted?

- I set `responseMimeType: application/json` and a low temperature (0.2) so the answer is JSON and stable.
- `parse_ai_response()` removes markdown code fences if the model adds them, then loads the JSON.
- The category and priority are matched against the allowed values ignoring case. If the model returns something outside the list (for example "Shipping"), it is replaced with a safe default (General / Medium), so invalid data never gets saved.
- If the reply is empty, a default polite reply is used.
- If anything fails (no key, timeout, network error, bad JSON), an `AIServiceError` is raised and a keyword based fallback is used instead. The response shows `ai_used: "fallback"` so it is clear where the result came from.

## What challenges did I face?

- **Getting clean JSON from the model.** Sometimes LLMs wrap JSON in code blocks or add extra text. I fixed this with JSON response mode in the request plus cleaning and validation in the parser.
- **Model returning values outside the allowed list.** Solved by matching against the choices and using defaults.
- **AI being slow or unavailable.** Added a timeout and a fallback so the API never returns a 500 because of the AI.
- **Testing without calling the real API.** Used `unittest.mock.patch` to mock `call_gemini`, so tests are fast and do not need a key.
- **Keeping the key safe.** The key is only in `.env`, which is in `.gitignore`. `.env.example` shows the format.
