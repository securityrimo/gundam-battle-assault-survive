# -*- coding: utf-8 -*-
import csv, io, sys
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
p='csv_ko_utf8/data/ark/custom_pilot/charamake_data.csv'
ko=list(csv.reader(open(p,encoding='utf-8')))
BS=chr(92)+'n'  # 리터럴 \n
REP={
 (86,1): 'BS'.join([]) or ('진군 루트가 두 개 발견되었다.'+BS+'지름길이지만 적과 만나기 쉬운 루트,'+BS+'돌아가지만 비교적 안전한 루트.'+BS+'어느 길로 가겠는가?'),
 (62,1): '입대 후 고락을 함께한 친구가'+BS+'생환을 기약할 수 없는'+BS+'격전지로 파병되게 되었다.'+BS+'각오를 다진 친구를 위해'+BS+'당신은 무엇을 하는가?',
 (41,1): '동료기와 마찬가지로 소중한 파트너,'+BS+'오퍼레이터. 그녀들의 지시가 없으면'+BS+'임무 성공률은 크게 떨어진다.'+BS+'당신이 그들에게 가장 바라는'+BS+'자질은 무엇인가?',
}
for (ri,ci),v in REP.items():
    print(f'r{ri}c{ci}: {len(ko[ri][ci])} -> {len(v)}')
    ko[ri][ci]=v
with open(p,'w',encoding='utf-8',newline='') as f: csv.writer(f).writerows(ko)
print('done')
