import json,os,sys
L=json.load(open(os.path.dirname(os.path.abspath(__file__))+'/timeline.json'))['lines'];T=lambda i:L[i]['t0']+0.1
m=lambda a,b:(L[a]['t0']+L[b]['t1'])/2+0.1  # +0.1 封面前置
print(' '.join(f'{x:.2f}' for x in [0.01,L[2]['t0']+0.6,T(4)+0.8,m(7,8),m(9,10),m(13,14),T(17)+1,m(21,22),m(26,27),L[28]['t1']+0.3,m(31,32),L[37]['t1']+1.5]))
