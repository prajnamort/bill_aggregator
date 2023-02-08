from bill_aggregator import consts
from bill_aggregator import exceptions


class BillAggregator:

    def __init__(self, conf, workdir):
        self.conf = conf
        self.workdir = workdir
        self.bill_group_confs = self.conf['bill_groups']

    def handle_bill_group(self, bill_group_conf):
        account = bill_group_conf['account']
        aggregation = bill_group_conf.get('aggregation', consts.DEFAULT_AGGREGATION)

        print(f'Handling bill_group: {account} -> {aggregation}')

        default_file_pattern = f'{account}*'
        file_pattern = bill_group_conf.get('file_pattern', default_file_pattern)
        files = sorted(self.workdir.glob(file_pattern))

    def aggregate(self):
        for bill_group_conf in self.bill_group_confs:
            self.handle_bill_group(bill_group_conf)
