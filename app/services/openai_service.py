import json

from openai import OpenAI

from app.config import settings
from app.errors.report_errors import EmptyReportContentError
from app.schemas.report import GenerateRouteReportInput


client = OpenAI(api_key=settings.openai_api_key)


def build_route_report_prompt(data: GenerateRouteReportInput) -> str:
    payload = data.model_dump(mode="json")

    return f"""
Você é um assistente administrativo especializado em gestão de frotas públicas.

Você receberá dados de uma rota específica já realizada ou finalizada em uma aplicação de gestão de frotas.

No contexto deste sistema:
<<<<<<< HEAD
- "request" representa a solicitação de uso de um veículo.
- "route" representa a execução/acompanhamento dessa solicitação.
- "tracks" representam pontos registrados durante a rota, com coordenadas x e y e horário de criação.
- O relatório deve ser útil para um administrador entender o que aconteceu nessa rota.
=======
- "requests" representam solicitações de uso de veículos.
- "routes" representam registros de execução/acompanhamento dessas solicitações.
- Cada route possui um request_id que aponta para a request relacionada.
- "tracks" representam pontos de rastreamento de uma route, com latitude,
  longitude, data/hora de captura e, quando houver, imagem associada.
>>>>>>> 63a9c3c (mudança no recibimento das informações do core)

Sua tarefa é gerar um relatório administrativo em formato Markdown.

Regras obrigatórias:
- Retorne somente o conteúdo Markdown do relatório.
- Não coloque o Markdown dentro de bloco de código.
- Não retorne JSON.
- Use somente os dados enviados.
- Não invente números, nomes, datas, usuários, veículos, rotas, coordenadas ou departamentos.
- Não exponha nem solicite dados sensíveis.
- Não assuma informações que não estejam presentes no JSON.
- Caso faltem dados para alguma análise, diga claramente que os dados são insuficientes.
- Escreva em português do Brasil.
- Organize o relatório com títulos e subtítulos Markdown.
- Use tabelas Markdown quando ajudar a leitura.
- Gere recomendações apenas quando elas forem sustentadas pelos dados enviados.

O relatório deve conter, quando possível:
1. Título.
<<<<<<< HEAD
2. Identificação da rota.
3. Dados da solicitação relacionada.
4. Dados do veículo.
5. Dados básicos do solicitante ou motorista, sem dados sensíveis.
6. Horário de início e finalização da rota.
7. Descrição informada ao finalizar a rota.
8. Análise dos tracks registrados.
9. Possíveis inconsistências, como rota sem tracks, rota sem finalização, ou horários incoerentes.
10. Observações administrativas.
11. Recomendações baseadas nos dados.
=======
2. Período analisado.
3. Resumo geral.
4. Análise das requisições por status.
5. Veículos mais utilizados ou mais solicitados.
6. Departamentos ou usuários com maior volume de solicitações, se houver dados.
7. Análise das rotas/viagens registradas, considerando status, início, finalização e descrições.
8. Análise dos pontos de rastreamento, considerando latitude, longitude, data/hora de captura e imagens associadas, se houver dados.
9. Conflitos, gargalos ou concentração de demanda.
10. Recomendações administrativas.
11. Observações sobre limitações dos dados.
>>>>>>> 63a9c3c (mudança no recibimento das informações do core)

Dados recebidos em JSON:

{json.dumps(payload, ensure_ascii=False, indent=2)}
"""


def generate_route_report(data: GenerateRouteReportInput) -> str:
    prompt = build_route_report_prompt(data)

    response = client.responses.create(
        model=settings.openai_model,
        input=prompt,
    )

    markdown_content = response.output_text

    if not markdown_content or not markdown_content.strip():
        raise EmptyReportContentError()

    return markdown_content.strip()
