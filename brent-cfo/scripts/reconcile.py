#!/usr/bin/env python3
"""
Brent CFO — reference reconciliation engine.
Combines bank CSVs + PayPal PDFs into one consolidated, no-double-count transaction set.
Adjust file paths, then: python reconcile.py
Outputs /tmp/consolidated.json and prints the Straight Truth summary.
"""
import subprocess, re, csv, json, glob, os
from collections import defaultdict

DATA_DIR = os.environ.get("CFO_DATA", ".")   # point at the Bank Statements folder

def categorize(desc, dc):
    d = desc.upper()
    if dc == 'Credit':
        if 'NU SKIN' in d: return 'INCOME: Nu Skin'
        if 'SULLIVAN' in d: return 'INCOME: Consulting (Pat Sullivan)'
        if 'SSA' in d or 'SOC SEC' in d: return 'INCOME: Social Security'
        if 'MEWBOURNE' in d: return 'INCOME: Oil/Gas Royalty'
        if 'OVERDRAFT' in d or 'NONSUFFICIENT' in d or 'NSF' in d or 'REVERSAL' in d: return 'INCOME: Fee Reversal (NOT income)'
        if 'TRANSFER FROM' in d: return 'INCOME: Internal Transfer (NOT income)'
        if 'STAN' in d: return 'INCOME: Stan Store'
        return 'INCOME: Other'
    if 'CONTINUOUS OVERDRAFT' in d: return 'FEE: Continuous Overdraft ($5/day)'
    if 'OVERDRAFT FEE' in d or 'OVERDRAFT ITEM' in d: return 'FEE: Overdraft ($30)'
    if 'NSF' in d or 'RETURNED ITEM' in d or 'UNCOLLECTED' in d: return 'FEE: NSF / Returned Item'
    if 'CROSSROADS' in d or '(FDR)' in d: return 'Debt Settlement (Crossroads/FDR)'
    if 'CARDMEMBER' in d or 'ELAN WEB' in d or 'CAPITAL ONE' in d or 'CREDIT ONE' in d: return 'Credit Card Payments'
    if 'SANTANDER' in d: return 'Auto Loan (Santander)'
    if 'CHECK' in d: return 'Checks Written'
    if 'NUSKIN' in d or 'NU SKIN' in d or 'PHARMANEX' in d: return 'Nu Skin Product/Autoship'
    if 'ASHLEY' in d or 'DREA' in d or 'MUELLER' in d or 'MUELAN' in d or 'POOLE' in d: return 'PayPal to People (Ashley/Drea)'
    if any(k in d for k in ['VERCEL','OPENAI','ANTHROPIC','ELEVEN','HEYGEN','GITHUB','RENDER','OXYLABS','PERPLEXITY','MOONSHOT','OPENROUTER','GOOGLE','AIRTABLE','DROPBOX','PADDLE','APIFY','TWILIO','X CORP','BUFFER','SPACESHIP']): return 'AI / Software Tools'
    if any(k in d for k in ['NETFLIX','SPOTIFY','APPLE','YOUTUBE','HULU','AUDIBLE']): return 'Subscriptions / Media'
    if any(k in d for k in ['VERIZON','T-MOBILE','COX ','APS ','ARIZONA PUBLIC','SOUTHWEST GAS','PNM*','CENTURYLINK']): return 'Utilities / Phone / Internet'
    if 'ZEL' in d: return 'Zelle to People'
    if 'GRAYHAWK' in d or 'ASSN DUES' in d: return 'HOA Dues'
    if any(k in d for k in ['INSTACART','FRYS','SAFEWAY','WALMART','COSTCO','SPROUTS','DOORDASH']): return 'Groceries / Food Delivery'
    if 'ATM' in d or 'WITHDRAWAL' in d or 'W/D' in d: return 'ATM / Cash'
    return 'Other / Uncategorized'

def bank_is_transfer_to_paypal(d):
    d = d.upper()
    return 'ADD TO BALANCE' in d or ('PAYPAL' in d and 'TRANSFER' in d)

rows = []
# ---- BANK ----
for fn in glob.glob(os.path.join(DATA_DIR, "*.csv")):
    with open(fn) as f:
        for r in csv.DictReader(f):
            dc = r['Credit or Debit'].strip(); amt = float(r['Amount'])
            desc = re.sub(r'\s+',' ',r['Description']).strip()
            cat = categorize(desc, dc)
            is_fee = cat.startswith('FEE:')
            # drop bank->PayPal transfers & internal (avoid double count) — BUT NEVER a fee row
            if dc=='Debit' and not is_fee and (bank_is_transfer_to_paypal(desc) or cat=='Internal Transfer Out'):
                continue
            if cat in ('INCOME: Fee Reversal (NOT income)','INCOME: Internal Transfer (NOT income)'):
                continue
            rows.append({'src':'bank','date':r['Processed Date'],'month':r['Processed Date'][:7],
                         'desc':desc,'dc':dc,'amt':amt,'cat':cat})
# ---- PAYPAL (non-bank-funded outflows + direct income) ----
seen=set()
for f in glob.glob(os.path.join(DATA_DIR, "PPstatement*.pdf")):
    txt = subprocess.run(['pdftotext','-layout',f,'-'],capture_output=True,text=True).stdout
    for i,blk in enumerate(re.split(r'(ID: \w+)', txt)):
        if i%2==1: continue
        tid_match = None
    blocks = re.split(r'(ID: \w+)', txt)
    for i in range(0,len(blocks)-1,2):
        block=blocks[i]; tid=(blocks[i+1] if i+1<len(blocks) else '').replace('ID: ','').strip()
        if not tid or tid in seen: continue
        seen.add(tid)
        am=re.search(r'USD\s+(-?[\d,]+\.\d{2})',block)
        if not am: continue
        v=float(am.group(1).replace(',',''))
        if 'General Credit Card Deposit' in block or 'Bank Deposit to PP' in block: continue
        month=re.search(r'(\d{2})/\d{2}/(\d{4})',block)
        mm = f"{month.group(2)}-{month.group(1)}" if month else '????-??'
        dm=re.search(r'\d{2}/\d{2}/\d{2,4}\s*\n?\s*(.+?)\s+USD',block,re.S)
        desc=re.sub(r'\s+',' ',dm.group(1)).strip()[:60] if dm else '?'
        bankfunded = 'Altabank' in block or 'x-1633' in block or 'x-1690' in block
        if v>0:  # income into PayPal (only real external payments, not funding legs)
            if 'General Payment' in block and 'Sullivan' in block:
                rows.append({'src':'paypal','date':mm+'-15','month':mm,'desc':desc,'dc':'Credit','amt':v,'cat':'INCOME: Consulting (Pat Sullivan)'})
        else:  # outflow — only non-bank funded (bank ones already counted)
            if not bankfunded:
                rows.append({'src':'paypal','date':mm+'-15','month':mm,'desc':desc,'dc':'Debit','amt':abs(v),'cat':categorize(desc,'Debit')})

json.dump(rows, open('/tmp/consolidated.json','w'))
inc=sum(r['amt'] for r in rows if r['dc']=='Credit')
sp=sum(r['amt'] for r in rows if r['dc']=='Debit')
fees=sum(r['amt'] for r in rows if r['cat'].startswith('FEE:'))
print(f"CONSOLIDATED  IN ${inc:,.0f}  OUT ${sp:,.0f}  NET ${inc-sp:,.0f}  | fees ${fees:,.0f}")
g=defaultdict(float)
for r in rows:
    if r['dc']=='Debit': g[r['cat']]+=r['amt']
print("Top outflows:")
for c,a in sorted(g.items(),key=lambda x:-x[1])[:8]: print(f"  ${a:>9,.0f}  {c}")
print("\n** VERIFY fees against raw CSVs before trusting. **")
