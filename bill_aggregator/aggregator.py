class BillAggregator:

    def __init__(self, conf, workdir):
        self.conf = conf
        self.workdir = workdir

    def aggregate(self):
        print(self.conf)
        print(self.workdir)
