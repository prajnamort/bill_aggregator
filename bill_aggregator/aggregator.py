from bill_aggregator.consts import (
    DEFAULT_AGGREGATION, FINAL_MEMO_SEPARATOR, ACCT, AGG, MEMO,
)
from bill_aggregator.extractors import ExtractorClsMapping
from bill_aggregator.exceptions import BillAggregatorException


class BillAggregator:

    def __init__(self, conf, workdir):
        self.conf = conf
        self.workdir = workdir
        self.bill_group_confs = self.conf['bill_groups']

        self.results_list = []

    def _process_final_memo(self, results, final_memo_conf):
        field_list = final_memo_conf
        # check final_memo_conf
        if any(f not in row for f in field_list for row in results):
            raise BillAggregatorException('final_memo specified unknown field')

        for row in results:
            memo = FINAL_MEMO_SEPARATOR.join(row[f] for f in field_list)
            row[MEMO] = memo
        return results

    def postprocess_results(self, results, bill_group_conf):
        if 'final_memo' in bill_group_conf:
            results = self._process_final_memo(results, bill_group_conf['final_memo'])
        return results

    def handle_bill_group(self, bill_group_conf):
        account = bill_group_conf[ACCT]
        aggregation = bill_group_conf.get(AGG, DEFAULT_AGGREGATION)
        file_type = bill_group_conf['file_type']
        file_config = bill_group_conf['file_config']

        ExtractorCls = ExtractorClsMapping[file_type]

        print(f'Handling bill_group: {account} -> {aggregation}')

        default_file_pattern = f'{account}*'
        file_pattern = bill_group_conf.get('file_pattern', default_file_pattern)
        files = sorted(self.workdir.glob(file_pattern))

        for file in files:
            extractor = ExtractorCls(file=file, file_conf=file_config)
            extractor.extract_bills()
            # add account and aggregation column to extractor results
            results = extractor.results.copy()
            for row in results:
                row[ACCT] = account
                row[AGG] = aggregation
            # postprocess results
            results = self.postprocess_results(results, bill_group_conf)
            # save results, waiting aggregation
            self.results_list.append(results)

            for row in results:
                print(row)
            print(f'rows: {len(results)}')

    def aggregate_bills(self):
        for bill_group_conf in self.bill_group_confs:
            self.handle_bill_group(bill_group_conf)
