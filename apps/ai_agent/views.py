from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import json
from .services import ask_ai_agent
from .models import Conversation, Message


@login_required
def ai_chat(request):
    conversations = Conversation.objects.filter(user=request.user)[:10]
    return render(request, "ai/chat.html", {"conversations": conversations})


@login_required
@require_POST
def api_chat(request):
    try:
        data = json.loads(request.body)
        message = data.get("message", "").strip()
        conversation_id = data.get("conversation_id")

        if not message:
            return JsonResponse({"error": "Message is required"}, status=400)

        # Get or create conversation
        if conversation_id:
            conversation = Conversation.objects.get(id=conversation_id, user=request.user)
        else:
            conversation = Conversation.objects.create(user=request.user, title=message[:50])

        # Save user message
        Message.objects.create(conversation=conversation, role="user", content=message)

        # Get history
        history = [
            {"role": m.role, "content": m.content}
            for m in conversation.messages.all()
        ]

        # Ask AI
        reply = ask_ai_agent(message, history[:-1])  # exclude current message

        # Save assistant reply
        Message.objects.create(conversation=conversation, role="assistant", content=reply)

        return JsonResponse({
            "reply": reply,
            "conversation_id": conversation.id,
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
