from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .sustain import SUSTAIN, MathOptimizer, TextOptimizer
import sys
import json
import os

application_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../application'))
if application_path not in sys.path:
    sys.path.append(application_path)

from main import track_token_length

# Initialize instances
sustain_instance = SUSTAIN(api_key=os.getenv("OPENAI_API_KEY"))
math_optimizer = MathOptimizer()
text_optimizer = TextOptimizer()

@csrf_exempt
def process_query(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            query = data.get("query", "")
            if not query:
                return JsonResponse({"error": "No query provided."})
            
            response, percentage_saved = sustain_instance.get_response(query)
            return JsonResponse({
                "response": response,
                "percentage_saved": percentage_saved
            })
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format"})
    return JsonResponse({"error": "Invalid request method"})

@csrf_exempt
def solve_math(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            expression = data.get("expression", "")
            if not expression:
                return JsonResponse({"error": "No expression provided."})
            
            result = math_optimizer.solve_math(expression)
            return JsonResponse({"result": result})
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format"})
    return JsonResponse({"error": "Invalid request method"})

@csrf_exempt
def optimize_text(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            text = data.get("text", "")
            if not text:
                return JsonResponse({"error": "No text provided."})
            
            optimized_text = text_optimizer.optimize_text(text)
            return JsonResponse({"optimized_text": optimized_text})
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format"})
    return JsonResponse({"error": "Invalid request method"})

@csrf_exempt
def token_length(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            message = data.get("message", "")
            if not message:
                return JsonResponse({"error": "No message provided."})
            
            token_length = track_token_length(message)
            return JsonResponse({"token_length": token_length})
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format"})
    return JsonResponse({"error": "Invalid request method"})