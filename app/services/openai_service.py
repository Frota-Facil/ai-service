import json
from datetime import datetime
from typing import Any

from openai import OpenAI, OpenAIError

from app.config import settings
from app.errors.report_errors import EmptyReportContentError, ReportGenerationError
from app.schemas.report import GenerateRouteReportInput, ReportTrack


client = OpenAI(api_key=settings.openai_api_key)

TRACK_GAP_ALERT_MINUTES = 30
MAX_TRACK_TIMESTAMPS = 25
MAX_TRACK_GAPS = 5

TECHNICAL_IDENTIFIER_KEYS = {
    "approved_by",
    "id",
    "image_key",
    "image_url",
    "request_id",
    "route_id",
    "user_id",
    "vehicle_id",
}

ROUTE_REPORT_INSTRUCTIONS = """
Você é um analista administrativo especializado em gestão de frotas públicas.

Objetivo:
Gerar um relatório executivo profissional para administradores entenderem rapidamente
se houve problema operacional em uma rota. A análise deve interpretar os dados, não
espelhar tabelas do banco.

Contexto dos dados:
- "request" representa a solicitação planejada de uso do veículo.
- "route" representa a execução/acompanhamento da solicitação.
- "tracking_summary" resume os pontos de rastreamento da rota.
- Variações de horário em minutos seguem esta regra: valores positivos indicam atraso;
  valores negativos indicam antecipação.

Regras obrigatórias:
- Retorne somente o conteúdo Markdown do relatório.
- Não coloque o Markdown dentro de bloco de código.
- Não retorne JSON.
- Escreva em português do Brasil.
- Use somente os dados do payload analisável.
- Não invente números, nomes, datas, usuários, veículos, rotas, coordenadas,
  trajetos, velocidades, distâncias ou departamentos.
- Não calcule, estime ou sugira distância percorrida, velocidade média ou trajeto
  realizado quando esses dados não estiverem explicitamente disponíveis.
- Não exponha UUIDs, IDs técnicos, chaves de imagem, URLs ou nomes de campos de banco.
- Evite repetir dados que normalmente já aparecem na tela administrativa.
- Priorize conclusões operacionais, riscos, limitações de auditoria e recomendações.
- Diferencie fatos observados de limitações de dados.
- Se os dados forem insuficientes para uma análise, diga exatamente qual análise ficou
  limitada, sem preencher lacunas com suposições.
- Gere recomendações apenas quando elas forem sustentadas pelos dados enviados.
- Não crie longas listas de itens ausentes. Aponte somente ausências relevantes para a
  auditoria ou para a interpretação da rota.

Estrutura obrigatória do relatório:

# Resumo Executivo
Escreva um resumo em linguagem natural contendo situação geral da rota, ocorrência
normal ou não, atrasos, antecipações, inconsistências, existência ou ausência de
rastreamento e necessidade de auditoria.

## Cronologia da rota
Mostre uma linha do tempo resumida dos principais eventos disponíveis. Use poucos
itens e priorize planejamento, início, fim e rastreamento.

## Análise Operacional
Explique duração da rota, horários, cumprimento do planejamento e descrição registrada
pelo motorista quando houver. Se algum dado essencial não existir, indique a limitação.

## Análise do Rastreamento
Se existirem tracks, analise quantidade de pontos, distribuição temporal, possíveis
falhas, grandes intervalos sem GPS e qualidade do rastreamento. Se não existirem
tracks, explique por que isso compromete a auditoria.

## Inconsistências encontradas
Liste somente problemas realmente encontrados. Se não houver inconsistência concreta,
use uma frase curta informando que nenhuma inconsistência foi identificada com os
dados disponíveis.

## Avaliação de Risco
Classifique como Baixo, Médio ou Alto e justifique objetivamente com base nos dados.

## Recomendações
Gere recomendações objetivas e acionáveis, baseadas apenas no payload.
"""


def _format_datetime(value: datetime | None) -> str | None:
    if value is None:
        return None

    return value.isoformat()


def _minutes_between(start: datetime | None, end: datetime | None) -> float | None:
    if start is None or end is None:
        return None

    try:
        return round((end - start).total_seconds() / 60, 2)
    except TypeError:
        return None


def _is_technical_identifier(key: str) -> bool:
    normalized_key = key.lower()

    return normalized_key in TECHNICAL_IDENTIFIER_KEYS or normalized_key.endswith("_id")


def _remove_technical_identifiers(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _remove_technical_identifiers(item)
            for key, item in value.items()
            if not _is_technical_identifier(key)
        }

    if isinstance(value, list):
        return [_remove_technical_identifiers(item) for item in value]

    return value


def _remove_empty_values(value: Any) -> Any:
    if isinstance(value, dict):
        cleaned = {
            key: _remove_empty_values(item)
            for key, item in value.items()
        }

        return {
            key: item
            for key, item in cleaned.items()
            if item not in (None, "", [], {})
        }

    if isinstance(value, list):
        return [
            item
            for item in (_remove_empty_values(item) for item in value)
            if item not in (None, "", [], {})
        ]

    return value


def _dump_for_prompt(model: Any, exclude: set[str] | None = None) -> dict[str, Any] | None:
    if model is None:
        return None

    payload = model.model_dump(
        mode="json",
        exclude_none=True,
        exclude=exclude or set(),
    )

    return _remove_empty_values(_remove_technical_identifiers(payload))


def _build_operational_summary(data: GenerateRouteReportInput) -> dict[str, Any]:
    route = data.route
    request = data.request

    planned_start = request.predicted_start_date if request else None
    planned_end = request.predicted_end_date if request else None

    return _remove_empty_values(
        {
            "actual_duration_minutes": _minutes_between(
                route.started_at,
                route.finished_at,
            ),
            "planned_duration_minutes": _minutes_between(planned_start, planned_end),
            "start_variation_minutes": _minutes_between(planned_start, route.started_at),
            "finish_variation_minutes": _minutes_between(planned_end, route.finished_at),
            "route_has_start": route.started_at is not None,
            "route_has_finish": route.finished_at is not None,
            "planning_available": planned_start is not None and planned_end is not None,
        }
    )


def _build_track_timestamp_summary(ordered_tracks: list[ReportTrack]) -> dict[str, Any]:
    timestamps = [_format_datetime(track.captured_at) for track in ordered_tracks]

    if len(timestamps) <= MAX_TRACK_TIMESTAMPS:
        return {"all_captured_at": timestamps}

    return {
        "first_captured_at": timestamps[:10],
        "last_captured_at": timestamps[-10:],
        "omitted_middle_points": len(timestamps) - 20,
    }


def _build_tracking_summary(tracks: list[ReportTrack]) -> dict[str, Any]:
    if not tracks:
        return {
            "has_tracking": False,
            "total_points": 0,
        }

    ordered_tracks = sorted(tracks, key=lambda track: track.captured_at)
    first_track = ordered_tracks[0]
    last_track = ordered_tracks[-1]

    intervals = []
    for previous_track, current_track in zip(ordered_tracks, ordered_tracks[1:]):
        interval_minutes = _minutes_between(
            previous_track.captured_at,
            current_track.captured_at,
        )

        if interval_minutes is None:
            continue

        intervals.append(
            {
                "from": _format_datetime(previous_track.captured_at),
                "to": _format_datetime(current_track.captured_at),
                "minutes": interval_minutes,
            }
        )

    large_intervals = [
        interval
        for interval in intervals
        if interval["minutes"] >= TRACK_GAP_ALERT_MINUTES
    ]
    largest_interval = max(
        (interval["minutes"] for interval in intervals),
        default=None,
    )
    latitudes = [track.latitude for track in ordered_tracks]
    longitudes = [track.longitude for track in ordered_tracks]

    return _remove_empty_values(
        {
            "has_tracking": True,
            "total_points": len(ordered_tracks),
            "points_with_image": sum(
                1 for track in ordered_tracks if track.image_url or track.image_key
            ),
            "first_captured_at": _format_datetime(first_track.captured_at),
            "last_captured_at": _format_datetime(last_track.captured_at),
            "tracking_duration_minutes": _minutes_between(
                first_track.captured_at,
                last_track.captured_at,
            ),
            "large_gap_threshold_minutes": TRACK_GAP_ALERT_MINUTES,
            "largest_interval_without_gps_minutes": largest_interval,
            "large_intervals_without_gps": large_intervals[:MAX_TRACK_GAPS],
            "total_large_intervals_without_gps": len(large_intervals),
            "coordinate_bounds": {
                "minimum_latitude": min(latitudes),
                "maximum_latitude": max(latitudes),
                "minimum_longitude": min(longitudes),
                "maximum_longitude": max(longitudes),
            },
            "captured_at_distribution": _build_track_timestamp_summary(ordered_tracks),
        }
    )


def _build_route_report_payload(data: GenerateRouteReportInput) -> dict[str, Any]:
    payload = {
        "route": _dump_for_prompt(
            data.route,
            exclude={"created_at", "updated_at"},
        ),
        "request": _dump_for_prompt(
            data.request,
            exclude={"approved_by", "created_at", "updated_at"},
        ),
        "vehicle": _dump_for_prompt(
            data.vehicle,
            exclude={"created_at", "updated_at"},
        ),
        "user_context": _dump_for_prompt(
            data.user,
            exclude={"name"},
        ),
        "operational_summary": _build_operational_summary(data),
        "tracking_summary": _build_tracking_summary(data.tracks),
        "extra_context": data.extra_context,
        "metadata": _remove_technical_identifiers(data.metadata),
    }

    return _remove_empty_values(payload)


def build_route_report_prompt(data: GenerateRouteReportInput) -> str:
    payload = _build_route_report_payload(data)
    payload_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))

    return f"""
{ROUTE_REPORT_INSTRUCTIONS}

Payload analisável em JSON:
{payload_json}
""".strip()


def generate_route_report(data: GenerateRouteReportInput) -> str:
    prompt = build_route_report_prompt(data)

    try:
        response = client.responses.create(
            model=settings.openai_model,
            input=prompt,
        )
    except OpenAIError as error:
        raise ReportGenerationError() from error

    markdown_content = response.output_text

    if not markdown_content or not markdown_content.strip():
        raise EmptyReportContentError()

    return markdown_content.strip()
