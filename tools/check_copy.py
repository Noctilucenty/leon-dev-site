#!/usr/bin/env python3
"""Fail the build when translated copy has a tell.

Written after the Chinese booking page shipped with ASCII punctuation — half-width
commas and question marks inside Chinese sentences ("全程中文,直接跟...") where a
Chinese reader expects 。，？：（）. It is invisible to someone who does not read
the language and unmistakable to someone who does, which is the worst combination:
the page reads as machine output to exactly the visitor it was written for.

The workflow-written service pages got this right. The page I hand-wrote did not,
so the rule lives here instead of in anyone's memory.

    python3 tools/check_copy.py     # exit 1 on any tell
"""

import glob
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Characters that exist ONLY in Traditional Chinese.
#
# This is a blocklist of the forms most likely to show up in business copy, NOT a
# complete Simplified/Traditional mapping — a rare traditional character can still
# slip through, and a real conversion table (OpenCC) would be the honest fix if
# that ever happens. It catches the realistic failure: copy pasted from a Taiwan
# or Hong Kong source, or a model drifting into traditional mid-paragraph.
#
# Deliberately excludes the many characters shared by both scripts. An earlier
# version listed 網站 and 價格 as whole words and so flagged 站 and 格, which are
# identical in Simplified. A checker with false positives gets ignored, which is
# worse than no checker.
TRADITIONAL_ONLY = set(
    '個們這來時國會說對開關無為與後點還過買賣車東馬長門風飛華語驗證檢測閉萬億'
    '營業價錢電話網訂單預約問題聯繫機構學習實現進運動員總結經濟資訊軟體'
    '歲於發將專務設計應該當樣類別斷續備夠幾麼樂藥豐鐵銀錄鐘錯鎖鮮魚鳥點'
    '龍龜齊儀優償兒黨內兩冊寫農馮凍劉則剛創動勞務勝勵勸區醫華協單賣'
    '嚴喪個丟並豐臨為舉麗庫廠廢廣廳彈強歸當錄彌徵復懷戀懶戰戲擊擔據'
    '擁擇擾攔攝敗數斬時晉曬書會東棄極樓標樣橋機檔歐歡歷殘殺毀氣沒'
    '溝滅濟濱瀋災爐營爭爺牽獨獲獻現產畢異當療盡監盤瞭矯確碼種積稱'
    '穩窮竊筆節範築簡籃籌粵糧納紅紙級純紛紙線練組細織終結絕統絡給絲'
    '經綠維綜緊緣編緩縣縫總績繁縱織繳續纖罰羅義習翹聞聲職聯聰肅腦'
    '臉與興舊艱蘭蘇蟲蠻術街衛衝衝複見規視覺覽觀觸訂計訊記訪設許訴'
    '診註評詞試詩話該詳誠誤說語誰課調談請論諾謀謝識證譯議護讀變讓'
)

# ASCII punctuation that must not sit against a CJK character.
ASCII_PUNCT = ',;:?!()'
CJK = r'一-鿿㐀-䶿'
BAD_PUNCT = re.compile(f'([{CJK}]\\s*[{re.escape(ASCII_PUNCT)}])|([{re.escape(ASCII_PUNCT)}]\\s*[{CJK}])')

# A phone number, a price and a URL legitimately carry ASCII punctuation even in
# Chinese copy: (510) 826-7735, $0.30, https://…
EXEMPT = re.compile(r'\(\d{3}\)\s*\d{3}-\d{4}|\$[\d.,]+|https?://\S+|[A-Za-z0-9_.-]+@[A-Za-z0-9.-]+|\d+(\.\d+)?%')

# Never, in any language. "cal state east bay" is his actual school and is allowed
# on /about; nothing else may name a place, because the whole offer is nationwide.
# "around the bay" slipped past a pattern that only knew "bay area" — it was
# live on the homepage FAQ, in the very answer about working with businesses
# anywhere in the US, offering to meet in person. The rule is not "no city
# names", it is "no geography that narrows the offer", so the pattern matches
# the bay in any phrasing. A repair bay is not geography, hence the exception.
CITY = re.compile(
    r'hayward|bay area|around the bay|in the bay|the east bay|湾区|灣區|'
    r'área da baía|área de la bahía|h\s?a\s?y\s?w\s?a\s?r\s?d|'
    r'meet in person|come to your (?:shop|office|store|business)',
    re.I)
# His actual school, and the automotive page's "repair bay", are both legitimate.
CITY_OK = re.compile(r'cal state east bay|repair bay|service bay|bay door', re.I)

# One acquisition experiment intentionally narrows its audience while the rest of
# the catalog stays nationwide. Keep this exception page-and-phrase exact: it may
# say "Bay Area", but it still may not name a city, offer in-person work or use any
# of the other prohibited local-service promises in CITY.
TARGETED_PLACE_OK = {
    'missed-lead-recovery.html': {'bay area'},
}


def visible_text(html_src):
    s = re.sub(r'<script.*?</script>|<style.*?</style>', ' ', html_src, flags=re.S)
    s = re.sub(r'<[^>]+>', ' ', s)
    return s


def main():
    os.chdir(ROOT)
    errors = []

    # 1. Chinese pages: simplified only, and CJK punctuation inside CJK sentences
    for path in sorted(glob.glob('zh/*.html')):
        raw = io.open(path, encoding='utf-8').read()
        text = visible_text(raw)

        trad = sorted({c for c in text if c in TRADITIONAL_ONLY})
        if trad:
            errors.append(f'{path}: traditional characters {trad} — this page is Simplified')

        probe = EXEMPT.sub(' ', text)
        for m in BAD_PUNCT.finditer(probe):
            frag = probe[max(0, m.start() - 22):m.end() + 22].strip()
            frag = ' '.join(frag.split())
            errors.append(f'{path}: ASCII punctuation in Chinese text -> …{frag}…')

        if '�' in raw:
            errors.append(f'{path}: replacement character — the file is mis-encoded')

    # 2. nobody names a city, in any language
    targets = (glob.glob('*.html') + glob.glob('services/*.html')
               + glob.glob('industries/*.html') + glob.glob('es/*.html')
               + glob.glob('pt/*.html') + glob.glob('zh/*.html') + ['llms.txt'])
    for path in targets:
        if not os.path.exists(path):
            continue
        s = io.open(path, encoding='utf-8').read()
        for m in CITY.finditer(s):
            if m.group(0).lower() in TARGETED_PLACE_OK.get(path, set()):
                continue
            around = s[max(0, m.start() - 40):m.end() + 40]
            if CITY_OK.search(around):
                continue
            errors.append(f'{path}: names a place ({m.group(0)!r}) — the offer is nationwide')

    # 3. every translated page must reach a booking page in its own language
    for lang, call in [('pt', '/pt/agendar'), ('es', '/es/agendar'), ('zh', '/zh/yuyue')]:
        for path in glob.glob(f'{lang}/*.html'):
            s = io.open(path, encoding='utf-8').read()
            if 'href="/call"' in s:
                errors.append(f'{path}: links to the English /call instead of {call}')

    if errors:
        print('COPY CHECK FAILED')
        for e in errors:
            print('  -', e)
        return 1
    n = len(glob.glob('zh/*.html')) + len(glob.glob('pt/*.html')) + len(glob.glob('es/*.html'))
    print(f'copy check ok — {n} translated pages, no tells')
    return 0


if __name__ == '__main__':
    sys.exit(main())
