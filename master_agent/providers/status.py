import os


def get_provider_status():
    providers = {
        "ChatGPT": "OPENAI_API_KEY",
        "Claude": "ANTHROPIC_API_KEY",
    }

    result = {}

    for name, env_name in providers.items():
        configured = bool(os.environ.get(env_name, "").strip())
        result[name] = {
            "configured": configured,
            "status": "API key configured" if configured else "API key not configured"
        }

    return result


if __name__ == "__main__":
    for provider, info in get_provider_status().items():
        print(f"{provider}: {info['status']}")
