class EmptyReportContentError(Exception):
    def __init__(self):
        super().__init__("A IA retornou um relatório vazio.")


class ReportGenerationError(Exception):
    def __init__(self):
        super().__init__("Não foi possível gerar o relatório com a IA.")
