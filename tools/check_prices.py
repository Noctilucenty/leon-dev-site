#!/usr/bin/env python3
"""Fail loudly when a published price contradicts itself.

Written because the reprice on 2026-08-20 shipped fifteen wrong figures. The
sweep that produced them looked for the OLD values and replaced them globally,
which both missed survivors and introduced new errors — a blanket
"$1,200 -> $300" also rewrote the phone agent, whose new floor is $1,000.

So this checks PER SERVICE, not per value: every figure that appears on a
service's own page must be that service's floor, or an explicitly allowed
cross-reference. Prices live on five surfaces that nothing syncs, and all five
are checked here.

    python3 tools/check_prices.py     # exit 1 on any contradiction
"""

import glob
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# The published floors. This dict is the single source of truth for the check.
FLOORS = {
    'small fixes': 75,
    'websites': 300,
    'seo': 300,
    'business-automation': 500,
    'booking-systems': 600,
    'websites-backend': 625,
    'business-dashboards': 750,
    'ai-chatbots': 750,
    'ai-phone-agents': 1000,
    'custom-software': 1500,
    'mobile-apps': 3500,
    'ongoing': 400,
}

# Figures a given service page may legitimately mention besides its own floor,
# because the copy deliberately points at a neighbouring service.
CROSS = {
    'websites': {625, 75, 300},          # the backend tier, small fixes
    'booking-systems': {600, 300},       # ordering sits with booking
    'custom-software': {1500, 3500},     # apps are the bigger sibling
    'business-automation': {500, 600},   # integrations quoted alongside booking
    'seo': {300},
    'ai-chatbots': {750, 600},
    'ai-phone-agents': {1000, 600, 500},
    'business-dashboards': {750, 500},
    'mobile-apps': {3500, 1500},
}

ALL = set(FLOORS.values())
# budget brackets on the quote form are ranges, not prices
IGNORE_FILES = {'quote.html'}

def figures(text):
    return [int(m.group(1).replace(',', '')) for m in re.finditer(r'\$([0-9][0-9,]*)', text)]

def main():
    os.chdir(ROOT)
    errors = []

    # 1. every service page may only show its own floor + declared cross-refs
    for path in sorted(glob.glob('services/*.html')):
        slug = os.path.basename(path)[:-5]
        if slug == 'index':
            continue
        allowed = CROSS.get(slug, {FLOORS.get(slug)}) | {FLOORS.get(slug)}
        allowed.discard(None)
        s = io.open(path, encoding='utf-8').read()
        for v in set(figures(s)):
            if v not in allowed:
                errors.append(f'{path}: ${v:,} is not this service\'s floor '
                              f'({FLOORS.get(slug)}) nor a declared cross-reference')

    # 2. no surface anywhere may show a figure that is not a published floor
    others = ([p for p in glob.glob('industries/*.html')]
              + ['index.html', 'about.html', 'call.html', 'es.html', 'pt.html',
                 'zh.html', 'llms.txt'])
    for path in others:
        if not os.path.exists(path) or os.path.basename(path) in IGNORE_FILES:
            continue
        s = io.open(path, encoding='utf-8').read()
        for v in set(figures(s)):
            if v not in ALL:
                errors.append(f'{path}: ${v:,} is not a published floor')

    # 3. a range must ascend — "$600-$300" shipped live once
    for path in glob.glob('services/*.html') + glob.glob('industries/*.html') + ['llms.txt']:
        if not os.path.exists(path):
            continue
        s = io.open(path, encoding='utf-8').read()
        for m in re.finditer(r'\$([0-9][0-9,]*)\s*[–—-]\s*\$([0-9][0-9,]*)', s):
            lo = int(m.group(1).replace(',', ''))
            hi = int(m.group(2).replace(',', ''))
            if hi < lo:
                errors.append(f'{path}: descending range ${lo:,}-${hi:,}')

    # 4. the assistant quotes prices too, and it has its own copy of the list
    prompt = io.open('server/prompt.js', encoding='utf-8').read()
    for v in set(figures(prompt)):
        if v not in ALL:
            errors.append(f'server/prompt.js: ${v:,} is not a published floor')

    if errors:
        print('PRICE CHECK FAILED')
        for e in errors:
            print('  -', e)
        return 1
    print(f'price check ok — {len(ALL)} floors, every surface agrees')
    return 0


if __name__ == '__main__':
    sys.exit(main())
