import os
import sys
import logging
import warnings
import utils
from utils import get_nested_value, obj2set, f8extract, struct
from tqdm import tqdm

m = '/mindhive/evlab/u/Shared/SUBJECTS'
LOG = logging.getLogger(__name__)

class Metadata:
    # a metadata structure, collecting information from the entire
    # input dataframe
    data = []
    models = []  # (string: parent_dir, Model: model)
    output = []

    def __init__(self, **kwargs):
        self.f = kwargs.get('csv', None)
        self.parent_dir = kwargs.get('session_cname', '')
        self.child_dir = kwargs.get('model_cname', '')
        self.__init()

    def __init(self):
        # add initializing code here
        if self.f:
            import pandas as pd
            self.data = pd.read_csv(self.f)

    def create_model_objects(self):
        if self.parent_dir and self.child_dir:
            for t in zip(self.data[self.parent_dir], self.data[self.child_dir]):
                self.models.append(Model(t))
        else:
            ValueError('Missing session & model column names')

    def collect_model_info(self):
        if not self.models:
            self.create_model_objects()
        for model in tqdm(self.models):
            model.parse_spm()
            model.parse_model()

    def collect_preproc_info(self):
        if not self.models:
            self.create_model_objects()
        else:
            for model in self.models:
                model.parse_hdf_preproc()

    def write_model_csv(self, filename):
        for model in self.models:
            self.output.append(model.params)
        import pandas as pd
        df = pd.DataFrame(self.output)
        df = df.set_index(['Session', 'Experiment', 'n_voxels']).apply(pd.Series.explode).reset_index()
        df.to_csv(filename)


class Model:

    def __init__(self, model_info):
        """

        :param model_info: tuple of relevant information
            x[0]: session name
            x[-1]: model name
            x[i]: not yet implemented

        """
        self.hdr = None
        self.params = {
            'Session': model_info[0],
            'Experiment': model_info[-1],
            'n_voxels': None,
            'IPS': None,
            'Files': None,
            'hpf': None,
            'nconds': None
        }

        # self.spm = os.path.join(os.getcwd(), 'SPM.mat')
        # self.model = os.path.join(os.getcwd(), 'modelspecification.mat')
        path = os.path.join(m, self.params['Session'], 'firstlevel_%s' % self.params['Experiment'])
        self.spm = os.path.join(path, 'SPM.mat')
        self.model = os.path.join(path, 'modelspecification.mat')

    def open_fp(self, file):
        self.hdr = None
        if os.path.exists(file):
            try:
                import h5py
                self.hdr = h5py.File(file, 'r')
            except OSError:
                self.hdr = utils.load_mat(file)
            except NotImplementedError:
                warnings.warn('Skipping %s, mat file not readable' % file)
        else:
            warnings.warn('%s file not found (warn)' % file)
            #LOG.info("%s file not found (LOG)" % file)
            #print("%s file not found (stdout)" % file)

    def parse_spm(self):
        self.open_fp(self.spm)
        if self.hdr is not None:
            self.params['IPS'] = f8extract(get_nested_value(self.hdr, struct['ips']))
            self.params['n_voxels'] = f8extract(get_nested_value(self.hdr, struct['s_base'] + struct['voxels']))[0]
            self.params['Files'] = obj2set(self.hdr, get_nested_value(self.hdr, struct['s_base'] + struct['volume']))

    def parse_model(self):
        self.open_fp(self.model)
        if self.hdr is not None:
            self.params['hpf'] = utils.nested2list(get_nested_value(self.hdr, struct['e_base']), 'hpf')
            self.params['nconds'] = [len(d_mat) for d_mat in
                                     utils.nested2list(get_nested_value(self.hdr, struct['e_base']), 'cond')]
        else:
            self.params['hpf'] = [None]*len(self.params['Files'])
            self.params['nconds'] = self.params['hpf']
