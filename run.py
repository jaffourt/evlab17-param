from metadata import Metadata
m = Metadata(csv='reliability.csv', session_cname='Session', model_cname='Exp')
m.collect_model_info()
m.write