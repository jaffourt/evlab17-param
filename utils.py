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


def get_nested_value(ref, fields):
    return reduce(getitem, fields, ref)


def path2file(s):
    return s.split('/')[-1]


def byte2str(bytes_obj, path=True):
    if path:
        return path2file(''.join(chr(i[0]) for i in bytes_obj))
    else:
        return ''.join(chr(i[0]) for i in bytes_obj)


def obj2set(ref, obj):
    if len(obj) == 1:
        obj = obj[0]
    return set([byte2str(ref[i]) for i in obj])


def nested2list(obj, key):
    return list(map(itemgetter(key), obj))


def f8extract(f8):
    if len(f8) == 1:
        f8 = f8[0]
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
