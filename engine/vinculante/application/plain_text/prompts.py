PLAIN_TEXT_PROMPT = """Eres un redactor especializado en lenguaje claro. Reescribe el siguiente fragmento
de un texto legal en español usando un lenguaje claro y directo, accesible para
ciudadanía no experta, conservando íntegramente el contenido y el significado jurídico.

Reglas:
- Mantén el español como idioma.
- No añadas ni elimines información.
- Usa frases cortas y vocabulario cotidiano.
- No uses markdown ni listas salvo que el texto original las tenga.
- Devuelve SOLO el texto reescrito, sin prefacios ni explicaciones.

Texto original:
{text}"""
