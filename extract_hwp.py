import struct, pathlib, zlib
p=next(pathlib.Path('.').glob('*.hwp'))
b=p.read_bytes(); ss=1<<struct.unpack_from('<H',b,30)[0]; ms=1<<struct.unpack_from('<H',b,32)[0]
def sector(n): return b[(n+1)*ss:(n+2)*ss]
dif=list(struct.unpack_from('<109I',b,76)); nxt,count=struct.unpack_from('<II',b,68)
for _ in range(count):
 a=struct.unpack('<%dI'%(ss//4),sector(nxt)); dif.extend(a[:-1]); nxt=a[-1]
fat=[]
for n in dif:
 if n<0xfffffffa: fat.extend(struct.unpack('<%dI'%(ss//4),sector(n)))
def chain(n,tab,read):
 out=b''; seen=set()
 while n<0xfffffffa and n not in seen:
  seen.add(n); out+=read(n); n=tab[n]
 return out
d=chain(struct.unpack_from('<I',b,48)[0],fat,sector); entries=[]
for i in range(0,len(d),128):
 e=d[i:i+128]; ln=struct.unpack_from('<H',e,64)[0]
 if ln: entries.append((e[:ln-2].decode('utf-16le'),e[66],struct.unpack_from('<I',e,116)[0],struct.unpack_from('<Q',e,120)[0]))
root=next(e for e in entries if e[1]==5); mini=chain(root[2],fat,sector)
mf=chain(struct.unpack_from('<I',b,60)[0],fat,sector); mtab=struct.unpack('<%dI'%(len(mf)//4),mf)
def stream(e): return (chain(e[2],mtab,lambda n: mini[n*ms:(n+1)*ms]) if e[3]<4096 else chain(e[2],fat,sector))[:e[3]]
header=stream(next(e for e in entries if e[0]=='FileHeader')); compressed=struct.unpack_from('<I',header,36)[0]&1
out=[]
for e in entries:
 if e[0].startswith('Section'):
  raw=stream(e); raw=zlib.decompress(raw,-15) if compressed else raw; pos=0
  while pos+4<=len(raw):
   v=struct.unpack_from('<I',raw,pos)[0]; pos+=4; tag=v&1023; size=v>>20
   if size==4095: size=struct.unpack_from('<I',raw,pos)[0]; pos+=4
   r=raw[pos:pos+size]; pos+=size
   if tag==67:
    vals=struct.unpack('<%dH'%(len(r)//2),r); chars=[]; j=0
    while j<len(vals):
     c=vals[j]
     if c in (1,2,3,11,12,14,15,16,17,18,19,20,21,22,23): j+=8; continue
     if c>=32: chars.append(chr(c))
     elif c==9: chars.append('\t')
     j+=1
    out.append(''.join(chars))
text='\n'.join(out); pathlib.Path('원문_추출.txt').write_text(text,encoding='utf-8'); print(text)
