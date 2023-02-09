from .csv_extractor import CsvExtractor
from bill_aggregator import consts


ExtractorClsMapping = {
    consts.FileType.CSV: CsvExtractor,
}
