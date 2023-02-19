from .xlsx_exporter import XlsxExporter
from bill_aggregator import consts


ExporterClsMapping = {
    consts.ExportType.XLSX: XlsxExporter,
}
