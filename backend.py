# backend.py
from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
import os

app = Flask(__name__)
# Permitir CORS desde tu servidor estático
CORS(app, origins=["http://127.0.0.1:8000", "http://localhost:8000"], supports_credentials=True)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def build_system_prompt(obra, autor=None, color=None, longitud="breves"):
    # Autor formateado (alias / sin nombre)
    autor_txt = ""
    if autor:
        if ":" in autor:
            nombre, alias = [x.strip() for x in autor.split(":", 1)]
            if nombre.lower().startswith("sin nombre"):
                autor_txt = f"Autor sin nombre público (crédito: {alias})."
            else:
                autor_txt = f"Autor: {nombre} (conocido como {alias})."
        else:
            if autor.lower().startswith("sin nombre"):
                autor_txt = "Autor sin nombre público."
            else:
                autor_txt = f"Autor: {autor}."

    extras = []
    if color:
        extras.append(f"colores aproximados: {color}")
    extras_txt = (" " + " / ".join(extras)) if extras else ""

    return (
        f"Actúa como guía cultural turístico. Eres la obra '{obra}'. {autor_txt}{extras_txt}\n"
        "Habla en tono cercano y evocador, pensado para visitantes en una ruta urbana; sugiere qué detalles mirar "
        "y cómo fotografiarla sin invadir el entorno; evita tecnicismos. "
        "Si te escriben 0000 puedes salirte del papel un momento. "
        "No repitas el título en cada respuesta. "
        f"Longitud de respuesta: {longitud.lower()}."
    )


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(force=True) #que es lo que hace request
    #lo que no entiendo es cómo data tendría el color,formas, longitud, etc. Me refiero
    #mi modelo solo da el nombre de la obra
    #Cómo tendría que adecuar mi modelo para que aporte también esa información?
    #estaba pensando poner los datos en un csv y que desde aquí solo se extraiga la info necesario en función de qué obra se trate
    obra = data.get("obra")
    autor = data.get("autor")
    color = data.get("color")
    longitud = data.get("longitud", "Intermedias")
    chatHistory = data.get("chatHistory", [])
    user_message = data.get("user_message")

    if not obra:
        return jsonify({"error": "Falta 'obra'"}), 400

    messages = [
    {"role": "system", "content": build_system_prompt(obra, autor, color, longitud)}
    ]
    
    # Si es el primer llamado (sin chatHistory ni user_message), pedimos una presentación
    if not chatHistory and not user_message:
        messages.append({
            "role": "user",
            "content": "Preséntate brevemente como la obra y da un saludo inicial."
        })
    else:
        # Continuación: agregamos chatHistory y el nuevo mensaje del usuario (si viene)
        #Cómo haría que el historial sea ilimitado, no quiero gastar todos mis tokens
        messages.extend(chatHistory)
        if user_message:
            messages.append({"role": "user", "content": user_message})

    try:
        resp = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.7
        )
        texto = resp.choices[0].message.content.strip()
        return jsonify({"respuesta": texto})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    # host/port explícitos
    app.run(host="127.0.0.1", port=5000, debug=True)
