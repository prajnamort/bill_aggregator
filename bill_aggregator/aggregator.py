class BillAggregator(object):

    def __init__(self, conf, workdir):
        self.conf = conf
        self.workdir = workdir

    def aggregate(self):
        print(self.conf)
        print(self.workdir)

        if 'sub_directory' in self.conf:
            agg_name = self.conf['sub_directory']
