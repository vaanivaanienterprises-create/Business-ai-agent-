def _generate_template_content(service="Home Nursing", language="Hindi"):
    service = service.strip() or "Home Nursing"

    if language == "English":
        whatsapp = f"""ApnaCare – Home Nursing & Elder Care

Need reliable {service} services at home in Agra?
We are here to help with caring and supportive home services.

Contact us on WhatsApp: 8630497651

Apno Jaisi Care, Ghar Par."""

        facebook = f"""Looking for {service} in Agra?

ApnaCare provides home-care support with a focus on comfort, care and trust.

Contact: 8630497651

ApnaCare – Apno Jaisi Care, Ghar Par."""

        instagram = f"""❤️ Care and comfort, right at home!

Looking for {service} in Agra?
Connect with ApnaCare for home-care support.

📍 Agra
📞 WhatsApp: 8630497651

Apno Jaisi Care, Ghar Par. ❤️

#ApnaCare #HomeCare #Agra #HomeNursing #ElderCare #PatientCare"""

    else:
        whatsapp = f"""🙏 ApnaCare – Home Nursing & Elder Care

क्या आपको घर पर {service} सेवा की जरूरत है?

ApnaCare आपके परिवार के लिए घर पर देखभाल की सुविधा उपलब्ध कराने का प्रयास करता है।

📍 सेवा क्षेत्र: Agra
📞 WhatsApp: 8630497651

Apno Jaisi Care, Ghar Par. ❤️"""

        facebook = f"""❤️ अपने परिवार की देखभाल अब घर पर!

ApnaCare लेकर आया है Agra में {service} की सुविधा।

हमारा उद्देश्य है आपके अपनों को घर पर आराम और देखभाल उपलब्ध कराना।

📞 संपर्क करें: 8630497651

ApnaCare – Apno Jaisi Care, Ghar Par.

#ApnaCare #HomeCare #Agra #ElderCare"""

        instagram = f"""❤️ अपनों की देखभाल, अब घर पर!

क्या आपको Agra में {service} सेवा की जरूरत है?

ApnaCare आपके परिवार के लिए घर पर देखभाल की सुविधा उपलब्ध कराने का प्रयास करता है।

📍 Agra
📞 WhatsApp: 8630497651

Apno Jaisi Care, Ghar Par. ❤️

#ApnaCare #Agra #HomeCare #HomeNursing #ElderCare #PatientCare #CareAtHome #FamilyCare"""

    return {
        "service": service,
        "language": language,
        "whatsapp_draft": whatsapp,
        "facebook_draft": facebook,
        "instagram_draft": instagram,
        "status": "DRAFT ONLY - NOT SENT OR PUBLISHED"
    }



def generate_marketing_content(service="Home Nursing", language="Hindi"):
    import json
    from master_agent.providers.ai_engine import ask_openai

    allowed = [
        "Home Nursing", "Elder Care", "Patient Care",
        "Baby Care", "Caregiver Service"
    ]
    service = service.strip()
    if service not in allowed:
        service = "Home Nursing"

    language = "English" if language == "English" else "Hindi"

    prompt = f"""
You are ApnaCare's ethical marketing assistant.
Business: ApnaCare Home Nursing & Elder Care.
Location: Agra, Uttar Pradesh.
Tagline: Apno Jaisi Care, Ghar Par.
Contact: 8630497651
Service: {service}
Language: {language}

Create three original marketing drafts:
1. whatsapp_draft
2. facebook_draft
3. instagram_draft

Rules:
- Use the requested language.
- Do not invent medical qualifications, guarantees, prices or claims.
- Keep the message professional and trustworthy.
- Return only valid JSON with those three string keys.
- These are drafts only. Never claim they were sent or published.
"""

    result = ask_openai(prompt)

    if result.get("ok"):
        try:
            raw = result.get("text", "")
            start = raw.find("{")
            end = raw.rfind("}")
            if start < 0 or end <= start:
                raise ValueError("JSON response missing")

            data = json.loads(raw[start:end + 1])
            keys = ["whatsapp_draft", "facebook_draft", "instagram_draft"]

            if not all(isinstance(data.get(k), str) and data[k].strip() for k in keys):
                raise ValueError("Invalid marketing response")

            return {
                "service": service,
                "language": language,
                **{k: data[k] for k in keys},
                "provider": "OpenAI",
                "status": "AI GENERATED - DRAFT ONLY, NOT SENT OR PUBLISHED"
            }
        except (ValueError, TypeError, json.JSONDecodeError):
            pass

    fallback = _generate_template_content(service, language)
    fallback["provider"] = "Template"
    fallback["status"] = "TEMPLATE FALLBACK - AI UNAVAILABLE; NOT SENT OR PUBLISHED"
    return fallback

if __name__ == "__main__":
    result = generate_marketing_content()
    print("===== ApnaCare Marketing Agent =====")
    print("\nWHATSAPP:\n", result["whatsapp_draft"])
    print("\nFACEBOOK:\n", result["facebook_draft"])
    print("\nINSTAGRAM:\n", result["instagram_draft"])
    print("\nSTATUS:", result["status"])
