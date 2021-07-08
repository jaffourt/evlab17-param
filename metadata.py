import os
import warnings
import utils
from utils import get_nested_value, obj2set, f8extract, struct
import progressbar

m = '/mindhive/evlab/u/Shared/SUBJECTS'


class Metadata:
    # a metadata structure, collecting information from the entire
    # input dataframe
    type = None  # could be None, audit, or convert
    data = None
    models = []  # (string: parent_dir, Model: model)
    output = None

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
        for model in progressbar.progressbar(self.models):
            model.parse_spm()
            model.parse_model()

    def collect_preproc_info(self):
        if not self.models:
            self.create_model_objects()
        else:
            for model in self.models:
                model.parse_hdf_preproc()

    def write_model_csv(self, filename):
        import pandas as pd
        df = pd.DataFrame(utils.combine_dict(self.models)).to_csv(filename)


class Model:
    hdr = None
    params = {}

    def __init__(self, model_info):
        """

        :param model_info: tuple of relevant information
            x[0]: session name
            x[-1]: model name
            x[i]: not yet implemented

        """

        self.params['Session'], sess = model_info[0], model_info[0]
        self.params['Experiment'], exp = model_info[-1], model_info[-1]

        # self.spm = os.path.join(os.getcwd(), 'SPM.mat')
        # self.model = os.path.join(os.getcwd(), 'modelspecification.mat')
        path = os.path.join(m, sess, 'firstlevel_%s' % exp)
        self.spm = os.path.join(path, 'SPM.mat')
        self.model = os.path.join(path, 'modelspecification.mat')
        pass

    def open_fp(self, file):
        self.hdr = None
        if os.path.exists(file):
            try:
                import h5py
                self.hdr = h5py.File(file, 'r')
            except OSError:
                self.hdr = utils.load_mat(file)
            except NotImplementedError:
                raise Warning('Skipping %s, mat file not readable' % file)
        else:
            warnings.warn('%s file not found' % file)

    def parse_spm(self):
        self.open_fp(self.spm)
        if self.hdr is not None:
            self.params['IPS'] = f8extract(get_nested_value(self.hdr, struct['ips']))
            self.params['n_voxels'] = f8extract(get_nested_value(self.hdr, struct['s_base'] + struct['voxels']))
            self.params['Files'] = obj2set(self.hdr, get_nested_value(self.hdr, struct['s_base'] + struct['volume']))
            # self.params['FWHM'] =
            # 'x=%.3f, y=%.3f, z%.3f' % tuple(f8extract(get_nested_value(self.hdr, struct['s_base'] + struct['smooth'])))
        else:
            self.params['IPS'], self.params['n_voxels'], self.params['Files'] = None, None, None

    def parse_model(self):
        self.open_fp(self.model)
        if self.hdr is not None:
            self.params['hpf'] = utils.nested2list(get_nested_value(self.hdr, struct['e_base']), 'hpf')
            self.params['nconds'] = [len(d_mat) for d_mat in
                                     utils.nested2list(get_nested_value(self.hdr, struct['e_base']), 'cond')]
        else:
            self.params['hpf'], self.params['nconds'] = None, None
