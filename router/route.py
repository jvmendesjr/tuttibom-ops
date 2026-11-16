#!/usr/bin/env python3
"""Roteador v0 — o Jev escolhe o modelo pela dificuldade; o 9Router responde.

Protótipo standalone. Não publica, não fala com canal nenhum e não lê
a chave: a credencial do 9Router vem de NINEROUTER_API_KEY; a do Jev
fica no keystore do CLI (`jev choose`).

Decisão: o esquema `jev.action_choice_request_v1` só aceita ids com
letras, dígitos e . _ : - (sem `/`). A tabela enviada ao Jev usa `:`
no lugar da barra (`cu:grok-4.7-low`). A descrição cita o id exato do
9Router, e o código traduz o id escolhido de volta antes da chamada.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from typing import Any

JEV_BIN = "/home/pc/.hermes/bin/jev"
BASE_URL = "https://9router.petemcasa.com/v1"
FALLBACK_MODEL = "core-medio"
CONFIDENCE_FLOOR = 0.65
USER_AGENT = "tuttibom-router-v0/0.1"
MODEL_TIMEOUT_S = 180
JEV_TIMEOUT_S = 20

# id do Jev (sem barra) → id exato no 9Router.
CANDIDATES: list[dict[str, str]] = [
    {
        "jev_id": "cu:grok-4.7-low",
        "model_id": "cu/grok-4.7-low",
        "description": (
            "Tarefa leve ou rápida: conta, cumprimento, classificação óbvia, "
            "resposta de uma linha. Tier baixo do Grok 4.7 do Cursor "
            "(9Router: cu/grok-4.7-low). Escolha quando a dificuldade for baixa, "
            "para a primeira resposta sair mais cedo."
        ),
    },
    {
        "jev_id": "cu:grok-4.7-medium",
        "model_id": "cu/grok-4.7-medium",
        "description": (
            "Tarefa de dificuldade média: explicar um conceito, resumir, "
            "escrever um trecho curto com algum raciocínio. Tier médio do "
            "Grok 4.7 do Cursor (9Router: cu/grok-4.7-medium)."
        ),
    },
    {
        "jev_id": "cu:grok-4.7-high",
        "model_id": "cu/grok-4.7-high",
        "description": (
            "Tarefa difícil: projeto, debug não óbvio, raciocínio de vários "
            "passos, trade-offs, código não trivial. Tier alto do Grok 4.7 "
            "do Cursor (9Router: cu/grok-4.7-high). Prioritário para o que "
            "for mais difícil."
        ),
    },
    {
        "jev_id": "cu:cursor-grok-4.5-high",
        "model_id": "cu/cursor-grok-4.5-high",
        "description": (
            "Alternativa de tier alto, Grok 4.5 do Cursor "
            "(9Router: cu/cursor-grok-4.5-high). Só se a tarefa for difícil "
            "e este modelo couber melhor que cu/grok-4.7-high."
        ),
    },
]

BY_JEV_ID = {row["jev_id"]: row["model_id"] for row in CANDIDATES}

EXAMPLES: list[dict[str, str]] = [
    {
        "nivel": "facil",
        "tarefa": "Quanto é 2+2? Responda só o número.",
    },
    {
        "nivel": "medio",
        "tarefa": (
            "Explique em três frases o que é um índice B-tree e quando vale "
            "a pena usá-lo num banco relacional."
        ),
    },
    {
        "nivel": "dificil",
        "tarefa": (
            "Projete as invariantes de um roteador que escolhe um modelo de "
            "linguagem pela dificuldade da tarefa, com piso de confiança e "
            "fallback. Liste os modos de falha (roteador lento, modelo lento "
            "para o primeiro token, escolha errada de tier) e diga como medir "
            "se o roteador de fato antecipa a primeira resposta. Seja conciso."
        ),
    },
]


def _redact(text: str) -> str:
    text = re.sub(r"Bearer\s+\S+", "Bearer [redigido]", text)
    text = re.sub(r"sk-[A-Za-z0-9_-]{8,}", "[redigido]", text)
    return text[:2000]


def _api_key() -> str:
    key = os.environ.get("NINEROUTER_API_KEY", "").strip()
    if not key:
        raise SystemExit(
            "NINEROUTER_API_KEY ausente no ambiente. "
            "Não grave a chave em arquivo; exporte a variável e rode de novo."
        )
    return key


def choose_model(tarefa: str) -> dict[str, Any]:
    """Pergunta ao Jev qual candidato usar. Falha ou baixa confiança → core-medio."""
    goal = (
        "Escolha um único modelo de linguagem, pela dificuldade da tarefa "
        "abaixo. Tarefa leve → tier baixo; média → tier médio; difícil → "
        "tier alto (prefira o Grok 4.7 high). Não invente outro id.\n\n"
        f"Tarefa:\n{tarefa.strip()[:1500]}"
    )
    request = {
        "schema": "jev.action_choice_request_v1",
        "goal": goal,
        "observation_id": "router-v0",
        "regions": [
            {
                "id": row["jev_id"],
                "role": "model",
                "label": row["description"][:300],
                "interactive": True,
            }
            for row in CANDIDATES
        ],
        "history": [],
        "candidates": [
            {"id": row["jev_id"], "description": row["description"]}
            for row in CANDIDATES
        ]
        + [
            {
                "id": "reobserve",
                "description": (
                    "Não escolha modelo. Só se o texto da tarefa estiver "
                    "vazio ou ilegível."
                ),
            },
            {
                "id": "abstain",
                "description": (
                    "Não escolha modelo. Só se a tarefa for impossível de "
                    "classificar pela dificuldade."
                ),
            },
        ],
    }
    started = time.perf_counter()
    try:
        proc = subprocess.run(
            [JEV_BIN, "choose"],
            input=json.dumps(request, ensure_ascii=False),
            capture_output=True,
            text=True,
            timeout=JEV_TIMEOUT_S,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        elapsed = time.perf_counter() - started
        return _fallback(
            jev_s=elapsed,
            reason=f"falha ao executar jev choose: {type(exc).__name__}",
            raw=None,
        )
    elapsed = time.perf_counter() - started
    stdout = (proc.stdout or "").strip()
    stderr = _redact((proc.stderr or "").strip())
    if proc.returncode != 0 or not stdout:
        return _fallback(
            jev_s=elapsed,
            reason=f"jev choose exit {proc.returncode}: {stderr or 'sem saída'}",
            raw=None,
        )
    try:
        reply = json.loads(stdout)
    except json.JSONDecodeError:
        return _fallback(
            jev_s=elapsed,
            reason="resposta do Jev não é JSON",
            raw=stdout[:500],
        )
    selected = str(reply.get("selected_id") or "")
    try:
        confidence = float(reply.get("confidence") or 0.0)
    except (TypeError, ValueError):
        confidence = 0.0
    jev_reason = str(reply.get("reason") or "")
    model_id = BY_JEV_ID.get(selected)
    low = confidence < CONFIDENCE_FLOOR or jev_reason == "low confidence"
    if model_id is None or low:
        why = jev_reason or "id fora da tabela"
        if low and jev_reason != "low confidence":
            why = f"confiança {confidence:.3f} abaixo de {CONFIDENCE_FLOOR:.2f}"
        if "unavailable" in jev_reason.lower() or jev_reason.startswith("Jev unavailable"):
            why = f"Jev indisponível ({jev_reason})"
        return _fallback(
            jev_s=elapsed,
            reason=why,
            raw=reply,
            confidence=confidence,
            selected_jev_id=selected,
        )
    return {
        "model_id": model_id,
        "selected_jev_id": selected,
        "confidence": round(confidence, 3),
        "fallback": False,
        "reason": jev_reason or "chosen",
        "jev_s": round(elapsed, 3),
        "probabilities": reply.get("probabilities") or {},
    }


def _fallback(
    *,
    jev_s: float,
    reason: str,
    raw: Any,
    confidence: float | None = None,
    selected_jev_id: str | None = None,
) -> dict[str, Any]:
    return {
        "model_id": FALLBACK_MODEL,
        "selected_jev_id": selected_jev_id,
        "confidence": None if confidence is None else round(confidence, 3),
        "fallback": True,
        "reason": _redact(reason),
        "jev_s": round(jev_s, 3),
        "probabilities": (raw or {}).get("probabilities", {}) if isinstance(raw, dict) else {},
    }


def _delta_text(obj: dict[str, Any]) -> str:
    choices = obj.get("choices") or []
    if not choices or not isinstance(choices[0], dict):
        return ""
    choice = choices[0]
    delta = choice.get("delta") if isinstance(choice.get("delta"), dict) else {}
    parts: list[str] = []
    for key in ("content", "reasoning_content", "reasoning", "text"):
        value = delta.get(key) if delta else choice.get(key)
        if isinstance(value, str) and value:
            parts.append(value)
    message = choice.get("message")
    if isinstance(message, dict):
        content = message.get("content")
        if isinstance(content, str) and content:
            parts.append(content)
    return "".join(parts)


def call_model(model_id: str, tarefa: str) -> dict[str, Any]:
    """Chama o modelo em streaming e mede o tempo até o primeiro texto."""
    key = _api_key()
    payload = {
        "model": model_id,
        "stream": True,
        "max_tokens": 220,
        "messages": [
            {
                "role": "system",
                "content": "Responda em português, de forma direta e curta.",
            },
            {"role": "user", "content": tarefa},
        ],
    }
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        f"{BASE_URL}/chat/completions",
        data=body,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
            "User-Agent": USER_AGENT,
        },
        method="POST",
    )
    started = time.perf_counter()
    text_parts: list[str] = []
    resolved = None
    ttft_s = None
    ttfb_s = None
    error = None
    try:
        with urllib.request.urlopen(request, timeout=MODEL_TIMEOUT_S) as response:
            buf = b""
            while True:
                block = response.read(1024)
                if not block:
                    break
                now = time.perf_counter()
                if ttfb_s is None:
                    ttfb_s = now - started
                buf += block
                while b"\n" in buf:
                    raw_line, buf = buf.split(b"\n", 1)
                    piece, model_name = _consume_sse_line(raw_line)
                    if model_name and resolved is None:
                        resolved = model_name
                    if piece:
                        if ttft_s is None:
                            ttft_s = now - started
                        text_parts.append(piece)
            if buf.strip():
                piece, model_name = _consume_sse_line(buf)
                if model_name and resolved is None:
                    resolved = model_name
                if piece:
                    if ttft_s is None:
                        ttft_s = time.perf_counter() - started
                    text_parts.append(piece)
    except urllib.error.HTTPError as exc:
        detail = _redact(exc.read(500).decode("utf-8", "replace"))
        error = f"HTTP {exc.code}: {detail}"
    except Exception as exc:  # noqa: BLE001 — registrar e seguir para o relatório
        error = f"{type(exc).__name__}: {_redact(str(exc))}"
    total_s = time.perf_counter() - started
    preview = "".join(text_parts).strip()
    return {
        "model_id": model_id,
        "resolved_model": resolved,
        "ok": error is None and bool(preview),
        "error": error,
        "ttft_s": None if ttft_s is None else round(ttft_s, 3),
        "ttfb_s": None if ttfb_s is None else round(ttfb_s, 3),
        "model_total_s": round(total_s, 3),
        "chars": len(preview),
        "preview": preview[:400],
    }


def _consume_sse_line(raw_line: bytes) -> tuple[str, str | None]:
    line = raw_line.decode("utf-8", "replace").strip()
    if not line or line.startswith(":"):
        return "", None
    if line.startswith("data:"):
        line = line[5:].strip()
    if line == "[DONE]" or not line:
        return "", None
    if not line.startswith("{"):
        return "", None
    try:
        obj = json.loads(line)
    except json.JSONDecodeError:
        return "", None
    if not isinstance(obj, dict):
        return "", None
    if "error" in obj and obj["error"]:
        raise RuntimeError(_redact(json.dumps(obj["error"], ensure_ascii=False)[:400]))
    model_name = obj.get("model") if isinstance(obj.get("model"), str) else None
    return _delta_text(obj), model_name


def run_task(tarefa: str, *, baseline: bool = False) -> dict[str, Any]:
    wall = time.perf_counter()
    if baseline:
        decision = {
            "model_id": FALLBACK_MODEL,
            "selected_jev_id": None,
            "confidence": None,
            "fallback": False,
            "reason": "referência direta, sem Jev",
            "jev_s": 0.0,
            "probabilities": {},
        }
    else:
        decision = choose_model(tarefa)
    generation = call_model(decision["model_id"], tarefa)
    ttft = generation["ttft_s"]
    first = None if ttft is None else round(decision["jev_s"] + ttft, 3)
    total = round(time.perf_counter() - wall, 3)
    return {
        "tarefa": tarefa,
        "baseline": baseline,
        "decisao": decision,
        "geracao": generation,
        "primeira_resposta_s": first,
        "total_s": total,
    }


def _note(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def run_bench() -> dict[str, Any]:
    _note("aquecimento core-medio")
    warmup = call_model(FALLBACK_MODEL, "Responda só: ok")
    _note(f"aquecimento ok={warmup['ok']} ttft={warmup['ttft_s']}")
    amostras = []
    for example in EXAMPLES:
        _note(f"roteador {example['nivel']}")
        routed = run_task(example["tarefa"], baseline=False)
        d = routed["decisao"]
        _note(
            f"  escolheu {d['model_id']} conf={d['confidence']} "
            f"fallback={d['fallback']} primeira={routed['primeira_resposta_s']}"
        )
        _note(f"referência {example['nivel']}")
        direct = run_task(example["tarefa"], baseline=True)
        _note(f"  core-medio primeira={direct['primeira_resposta_s']}")
        amostras.append(
            {
                "nivel": example["nivel"],
                "tarefa": example["tarefa"],
                "roteador": routed,
                "referencia_core_medio": direct,
            }
        )
    return {
        "quando": time.strftime("%Y-%m-%d %H:%M:%S %z"),
        "base_url": BASE_URL,
        "piso_confianca": CONFIDENCE_FLOOR,
        "fallback": FALLBACK_MODEL,
        "candidatos": [row["model_id"] for row in CANDIDATES],
        "aquecimento_descartado": {
            "model_id": warmup["model_id"],
            "ok": warmup["ok"],
            "ttft_s": warmup["ttft_s"],
            "error": warmup["error"],
        },
        "amostras": amostras,
    }


def _print_human(result: dict[str, Any]) -> None:
    decision = result["decisao"]
    gen = result["geracao"]
    print(f"modelo: {decision['model_id']}")
    if decision.get("fallback"):
        print(f"fallback: sim ({decision['reason']})")
    else:
        print(f"confiança: {decision['confidence']}")
    print(f"jev_s: {decision['jev_s']}")
    print(f"ttft_s: {gen['ttft_s']}")
    print(f"modelo_s: {gen['model_total_s']}")
    print(f"primeira_resposta_s: {result['primeira_resposta_s']}")
    print(f"total_s: {result['total_s']}")
    if gen["error"]:
        print(f"erro: {gen['error']}")
    else:
        print(f"resposta: {gen['preview']}")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Roteador v0 (Jev + 9Router)")
    parser.add_argument("tarefa", nargs="?", help="texto da tarefa")
    parser.add_argument(
        "--bench",
        action="store_true",
        help="mede 3 exemplos (fácil, médio, difícil) contra core-medio direto",
    )
    parser.add_argument(
        "--baseline",
        action="store_true",
        help="pula o Jev e chama core-medio direto",
    )
    parser.add_argument("--json", action="store_true", help="imprime JSON")
    args = parser.parse_args(argv)
    if args.bench:
        report = run_bench()
        json.dump(report, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
        return 0
    if not args.tarefa:
        parser.error("informe a tarefa ou use --bench")
    result = run_task(args.tarefa, baseline=args.baseline)
    if args.json:
        json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
    else:
        _print_human(result)
    return 0 if result["geracao"]["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
