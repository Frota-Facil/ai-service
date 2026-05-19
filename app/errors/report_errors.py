class EmptyReportContentError(Exception):
    def __init__(self):
        super().__init__("A IA retornou um relatório vazio.")