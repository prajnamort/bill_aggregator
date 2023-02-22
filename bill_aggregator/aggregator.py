from bill_aggregator.consts import (
    DEFAULT_AGGREGATION, FINAL_MEMO_SEPARATOR, FILE_EXTENSIONS,
    ACCT, AGG, MEMO, DATE, TIME,
)
from bill_aggregator.exceptions import BillAggregatorException
from bill_aggregator.extractors import ExtractorClsMapping
from bill_aggregator.exporters import ExporterClsMapping


class BillAggregator:

    def __init__(self, conf, workdir):
        self.conf = conf
        self.workdir = workdir
        self.bill_group_confs = self.conf['bill_groups']
        self.export_type = self.conf['export_to']
        self.export_conf = self.conf.get('export_config', None)

        self.extracted_results = []
        self.aggregated_results = {}

    def _process_final_memo(self, results, final_memo_conf):
        field_list = final_memo_conf
        # check final_memo_conf
        if any(f not in row for f in field_list for row in results):
            raise BillAggregatorException('final_memo specified unknown field')

        for row in results:
            memo = FINAL_MEMO_SEPARATOR.join(row[f] for f in field_list if row[f])
            row[MEMO] = memo
        return results

    def postprocess_extracted_results(self, results, account, aggregation, final_memo_conf):
        # add account and aggregation column
        for row in results:
            row[ACCT] = account
            row[AGG] = aggregation
        # final_memo
        if final_memo_conf is not None:
            results = self._process_final_memo(results, final_memo_conf)
        return results

    def extract_file(self, file, file_type, file_conf):
        ExtractorCls = ExtractorClsMapping[file_type]
        extractor = ExtractorCls(file=file, file_conf=file_conf)
        extractor.extract_bills()
        return extractor.results.copy()

    def extract_bill_group(self, bill_group_conf):
        account = bill_group_conf[ACCT]
        aggregation = bill_group_conf.get(AGG, DEFAULT_AGGREGATION)
        file_type = bill_group_conf['file_type']
        file_conf = bill_group_conf['file_config']
        final_memo_conf = bill_group_conf.get('final_memo', None)

        print(f'Extracting bill_group: {account} ({aggregation})')

        default_file_pattern = f'{account}*'
        file_pattern = bill_group_conf.get('file_pattern', default_file_pattern)
        files = sorted(self.workdir.glob(file_pattern))
        files = [file for file in files if file.suffix.lower() in FILE_EXTENSIONS[file_type]]

        for file in files:
            results = self.extract_file(
                file=file,
                file_type=file_type,
                file_conf=file_conf)
            results = self.postprocess_extracted_results(
                results=results,
                account=account,
                aggregation=aggregation,
                final_memo_conf=final_memo_conf)
            self.extracted_results.extend(results)

            # for row in results:
            #     print(row)
            # print(f'rows: {len(results)}')
            # print(f'total rows: {len(self.extracted_results)}')

    def extract_bills(self):
        for bill_group_conf in self.bill_group_confs:
            self.extract_bill_group(bill_group_conf)

    def aggregate_bills(self):
        def _sort_key(row):
            return (row[DATE], row[TIME])

        # aggregate by row[AGG]
        for row in self.extracted_results:
            agg_key = row[AGG]
            if agg_key not in self.aggregated_results:
                self.aggregated_results[agg_key] = []
            self.aggregated_results[agg_key].append(row)
        # sort every aggregation
        for l in self.aggregated_results.values():
            l.sort(key=_sort_key)    # stable sort (if same key, order is preserved)

        # for key, results in self.aggregated_results.items():
        #     for row in results:
        #         print(row)
        #     print(f'{key}: {len(results)} rows')

    def export_bills(self):
        ExporterCls = ExporterClsMapping[self.export_type]
        for aggregation, results in self.aggregated_results.items():
            exporter = ExporterCls(
                data=results,
                aggregation=aggregation,
                export_conf=self.export_conf,
                workdir=self.workdir)
            exporter.export_bills()
