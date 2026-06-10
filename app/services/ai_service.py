from datetime import datetime, timezone

from openai import AsyncOpenAI

from app.config import settings
from app.models.user import User
from app.models.task import Task
from app.models.chat_message import ChatMessage

client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

SYSTEM_PROMPT_BASE = (
    "Voce e o assistente do RoutineX, um aplicativo de produtividade. "
    "Ajude o usuario a organizar tarefas, criar rotinas e manter a motivacao. "
    "Responda sempre em portugues brasileiro."
)

PROFILE_PROMPTS = {
    "TDAH": "O usuario tem TDAH. Use tom direto, listas curtas e instrucoes passo a passo. Evite textos longos.",
    "ansiedade": "O usuario tem perfil de ansiedade. Use linguagem acolhedora e tranquilizadora. Divida tarefas em passos pequenos.",
}


def build_system_prompt(user: User, pending_tasks: list[Task] | None = None) -> str:
    prompt = SYSTEM_PROMPT_BASE

    if user.accessibility_profile and user.accessibility_profile in PROFILE_PROMPTS:
        prompt += "\n" + PROFILE_PROMPTS[user.accessibility_profile]

    if pending_tasks:
        tasks_summary = "\n".join(
            f"- {t.title} (prioridade: {t.priority}, vencimento: {t.due_date})" for t in pending_tasks[:10]
        )
        prompt += f"\n\nTarefas pendentes do usuario:\n{tasks_summary}"

    return prompt


async def chat_with_ai(
    user: User,
    message: str,
    recent_messages: list[ChatMessage],
    pending_tasks: list[Task] | None = None,
) -> str:
    system_prompt = build_system_prompt(user, pending_tasks)

    messages = [{"role": "system", "content": system_prompt}]

    context_messages = recent_messages[-10:]
    for msg in context_messages:
        messages.append({"role": msg.role, "content": msg.content})

    messages.append({"role": "user", "content": message})

    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        max_tokens=1000,
        temperature=0.7,
    )
    return response.choices[0].message.content


async def decompose_project(user: User, project_description: str) -> dict:
    system_prompt = (
        build_system_prompt(user)
        + "\n\nDeconha o projeto descrito pelo usuario em uma lista de tarefas e subtarefas. "
        'Responda em JSON com o formato: {"tasks": [{"title": "...", "subtasks": ["...", "..."]}]}'
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Decomponha este projeto em tarefas: {project_description}"},
    ]

    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        max_tokens=2000,
        temperature=0.5,
        response_format={"type": "json_object"},
    )
    return response.choices[0].message.content


async def suggest_routine(user: User, preferences: str, pending_tasks: list[Task] | None = None) -> dict:
    system_prompt = (
        build_system_prompt(user, pending_tasks)
        + "\n\nSugira uma rotina diaria ou semanal personalizada. "
        'Responda em JSON com o formato: {"routine": [{"time": "HH:MM", "title": "...", "priority": "media"}]}'
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Sugira uma rotina baseada em: {preferences}"},
    ]

    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        max_tokens=2000,
        temperature=0.5,
        response_format={"type": "json_object"},
    )
    return response.choices[0].message.content


async def optimize_day(user: User, pending_tasks: list[Task]) -> dict:
    tasks_summary = "\n".join(
        f"- {t.title} (prioridade: {t.priority}, tempo estimado: {t.estimated_time}h, vencimento: {t.due_date})"
        for t in pending_tasks
    )

    rest_info = ""
    if user.rest_start and user.rest_end:
        rest_info = f"\nHorario de descanso do usuario: {user.rest_start} - {user.rest_end}."

    system_prompt = (
        build_system_prompt(user)
        + f"\n\nOrganize as tarefas do dia de forma otimizada. Limite MAXIMO de 8 horas de atividades.{rest_info}"
        'Responda em JSON com o formato: {"schedule": [{"time": "HH:MM", "task_title": "...", "duration_hours": 1.5}]}'
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Organize meu dia com estas tarefas:\n{tasks_summary}"},
    ]

    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        max_tokens=2000,
        temperature=0.3,
        response_format={"type": "json_object"},
    )
    return response.choices[0].message.content


async def generate_motivational_message(user: User, recent_progress: str) -> str:
    system_prompt = (
        build_system_prompt(user)
        + "\n\nGere uma mensagem motivacional curta e personalizada baseada no progresso recente do usuario."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Meu progresso recente: {recent_progress}"},
    ]

    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        max_tokens=200,
        temperature=0.8,
    )
    return response.choices[0].message.content
