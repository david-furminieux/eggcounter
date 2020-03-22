'''
classes used for the CLI user interface
'''

class CLIRunner(object):

    def __init__(self, options=None):
        '''
        :param dict<str, any> options: possible options to configure the system 
        '''
        super().__init__()
        if options is None:
            options = {}
        self.configure(options)
    
    def configure(self, options):
        '''
        configure the Runner
        :param dict<str, any> options: the possible options.
        '''

    def run(self):
        pass

