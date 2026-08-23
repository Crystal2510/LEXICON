import time, tempfile, os
t0 = time.time()
from src.pipeline import ProductPipeline
t1 = time.time()
print('Import: %.3fs' % (t1-t0))

p = ProductPipeline()
t2 = time.time()
print('Init: %.3fs' % (t2-t1))

import pandas as pd
df = pd.read_csv('data/sample_input.csv')
out = os.path.join(tempfile.gettempdir(), 'bench.csv')
t3 = time.time()
result = p.process_csv('data/sample_input.csv', out, deep_sourcing=False)
t4 = time.time()
print('1000 rows: %.3fs' % (t4-t3))
print('Per row: %.1fms' % ((t4-t3)/1000*1000))
os.unlink(out)
