from .tabular_extractor import CsvExtractor, XlsExtractor
from bill_aggregator import consts


ExtractorClsMapping = {
    consts.FileType.CSV: CsvExtractor,
    consts.FileType.XLS: XlsExtractor,
}
