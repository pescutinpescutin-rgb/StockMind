from settings import get_setting


def ask_analyst(question, ticker, company, level="Beginner", language="English"):
    api_key = get_setting("OPENAI_API_KEY")

    if not api_key:
        if language == "Deutsch":
            return (
                f"**Lokaler Erklärmodus für {ticker}**\n\n"
                "Es ist kein KI-API-Schlüssel eingerichtet. "
                "Die verfügbaren Daten können Kennzahlen und den Unternehmensüberblick "
                "enthalten, aber ich kann ohne KI-Dienst keine freie Frage beantworten. "
                "Nutze den Lernmodus für verlässliche Grundbegriffe.\n\n"
                f"Deine Frage: {question}"
            )

        return (
            f"**Local explanation mode for {ticker}**\n\n"
            "No AI API key is configured. Available source data may include metrics "
            "and a company description, but I cannot answer free-form questions "
            "without an AI service. Use Educational mode for built-in metric "
            "explanations.\n\n"
            f"Your question: {question}"
        )

    try:
        from openai import OpenAI

        client = OpenAI(
            api_key=api_key,
            base_url=get_setting("OPENAI_BASE_URL") or None,
        )

        if language == "Deutsch":
            language_rule = "Answer in German."
        elif language == "Español":
            language_rule = "Answer in Spanish."
        elif language == "Italiano":
            language_rule = "Answer in Italian."
        elif language == "中文":
            language_rule = "Answer in Chinese (Simplified)."
        elif language == "日本語":
            language_rule = "Answer in Japanese."
        elif language == "한국어":
            language_rule = "Answer in Korean."
        elif language == "हिन्दी":
            language_rule = "Answer in Hindi."
        else:
            language_rule = "Answer in English."

        company_context = company if isinstance(company, str) else str(company)
        prompt = (
            f"{language_rule} You are a careful financial research educator. "
            "Do not give investment advice, specific buy/sell recommendations, price targets, or predictions. "
            "Talk in plain language at a {level.lower()} level. "
            "Use short sections and explain the key business drivers, not just the numbers. "
            "If a metric is missing or unclear, say so explicitly. "
            "Reference only the supplied company data and never invent missing facts.\n\n"
            f"Ticker: {ticker}\n"
            f"Company context:\n{company_context}\n\n"
            f"Question: {question}\n\n"
            "Response format:\n"
            "1. Short answer\n"
            "2. What matters\n"
            "3. Key data points\n"
            "4. Limitations / missing data\n"
            "5. Bottom line"
        )

        response = client.chat.completions.create(
            model=get_setting("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )

        content = response.choices[0].message.content.strip()
        if not content:
            return "The AI response was empty. Please try again."
        return content

    except Exception as exc:
        return (
            f"AI service unavailable ({type(exc).__name__}). "
            "Try again later or use Educational mode."
        )
