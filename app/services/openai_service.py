import json

from openai import OpenAI

from app.config import settings
from app.schemas.report import GenerateRawReportInput
from app.errors.report_errors import EmptyReportContentError


client = OpenAI(api_key=settings.openai_api_key)


def build_raw_report_prompt(data: GenerateRawReportInput) -> str:
    payload = data.model_dump(mode="json")

    return f"""
Você é um assistente administrativo especializado em gestão de frotas públicas.

Você receberá dados brutos de uma aplicação de gestão de frotas.
Esses dados podem incluir usuários, veículos, requisições e rotas/viagens.

No contexto deste sistema:
- "requests" representam solicitações de uso de veículos.
- "routes" representam registros de execução/acompanhamento dessas solicitações.
- Cada route possui um request_id que aponta para a request relacionada.

Sua tarefa é gerar um relatório administrativo em formato Markdown.

Regras obrigatórias:
- Retorne somente o conteúdo Markdown do relatório.
- Não coloque o Markdown dentro de bloco de código.
- Não retorne JSON.
- Use somente os dados enviados.
- Não invente números, nomes, datas, usuários, veículos, rotas ou departamentos.
- Não exponha nem solicite dados sensíveis.
- Não assuma informações que não estejam presentes no JSON.
- Caso faltem dados para alguma análise, diga claramente que os dados são insuficientes.
- Escreva em português do Brasil.
- Organize o relatório com títulos e subtítulos Markdown.
- Use tabelas Markdown quando ajudar a leitura.
- Use listas quando fizer sentido.
- Gere recomendações apenas quando elas forem sustentadas pelos dados enviados.

O relatório deve conter, quando possível:
1. Título.
2. Período analisado.
3. Resumo geral.
4. Análise das requisições por status.
5. Veículos mais utilizados ou mais solicitados.
6. Departamentos ou usuários com maior volume de solicitações, se houver dados.
7. Análise das rotas/viagens registradas, considerando status, início, finalização e descrições.
8. Conflitos, gargalos ou concentração de demanda.
9. Recomendações administrativas.
10. Observações sobre limitações dos dados.

Dados recebidos em JSON:

{json.dumps(payload, ensure_ascii=False, indent=2)}
"""


def generate_markdown_report(data: GenerateRawReportInput) -> str:
    prompt = build_raw_report_prompt(data)

    response = client.responses.create(
        model=settings.openai_model,
        input=prompt,
    )

    markdown_content = response.output_text

    if not markdown_content or not markdown_content.strip():
        raise EmptyReportContentError()

    return markdown_content.strip()