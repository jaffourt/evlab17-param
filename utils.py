from functools import reduce
from operator import itemgetter, getitem

struct = {
    's_base': ['SPM'],
    'contrast': ['xCon', 'name'],
    'ips': ['SPM', 'nscan'],
    'volume': ['xY', 'VY', 'fname'],
    'smooth': ['xVol', 'FWHM'],
    'voxels': ['xVol', 'S'],
    'e_base': ['matlabbatch', 'spm', 'stats', 'fmri_spec', 'sess'],
}


class OrderedSet:
    elements = []

    def __init__(self, elements: list):
        self.elements = []
        for element in elements:
            self.add(element)

    def add(self, entry):
        if entry not in self.elements:
            self.elements.append(entry)


def get_nested_value(ref, fields):
    try:
        return reduce(getitem, fields, ref)
    except IndexError:
        array = reduce(getitem, fields[:-1], ref)
        return nested2list(array, fields[-1])


def path2file(s):
    return s.split('/')[-1]


def byte2str(bytes_obj, path=True):
    if path:
        return path2file(''.join(chr(i[0]) for i in bytes_obj))
    else:
        return ''.join(chr(i[0]) for i in bytes_obj)


def obj2set(ref, obj):
    if type(obj) == list:
        return OrderedSet([path2file(f) for f in obj]).elements
    if len(obj) == 1:
        obj = obj[0]
    return OrderedSet([byte2str(ref[i]) for i in obj]).elements


def nested2list(obj, key):
    return list(map(itemgetter(key), obj))


def f8extract(f8):
    if type(f8) == list:
        if len(f8) == 1:
            f8 = f8[0]
        return list(map(float, f8))
    elif type(f8) == int:
        return [f8]
    else:
        return list(map(float, f8))


def combine_dict(dicts):
    d = {}
    for k in dicts[0].keys():  # assume shared keys
        d[k] = [d[k] for d in dicts]
    return d


def load_mat(filename):
    def _check_vars(d):
        for key in d:
            if isinstance(d[key], matlab.mio5_params.mat_struct):
                d[key] = _todict(d[key])
            elif isinstance(d[key], np.ndarray):
                d[key] = _toarray(d[key])
        return d

    def _todict(matobj):
        d = {}
        for strg in matobj._fieldnames:
            elem = matobj.__dict__[strg]
            if isinstance(elem, matlab.mio5_params.mat_struct):
                d[strg] = _todict(elem)
            elif isinstance(elem, np.ndarray):
                d[strg] = _toarray(elem)
            else:
                d[strg] = elem
        return d

    def _toarray(ndarray):
        if ndarray.dtype != 'float64':
            elem_list = []
            for sub_elem in ndarray:
                if isinstance(sub_elem, matlab.mio5_params.mat_struct):
                    elem_list.append(_todict(sub_elem))
                elif isinstance(sub_elem, np.ndarray):
                    elem_list.append(_toarray(sub_elem))
                else:
                    elem_list.append(sub_elem)
            return np.array(elem_list)
        else:
            return ndarray

    from scipy.io import loadmat, matlab
    import numpy as np
    data = loadmat(filename, struct_as_record=False, squeeze_me=True)
    return _check_vars(data)
