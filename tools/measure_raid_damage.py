"""Reproduce raid HP capacity measurements; no live connection or persistence."""
import json
import random
import sys
from pathlib import Path

from tuipet import battle

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / 'server'))
import raid_combat  # noqa: E402

samples = 20000
boss = next(int(n) for n, r in raid_combat.SPECIES.items() if r['stage'] == 'Mega')
rows = {}
for stage in ('InTraining', 'Rookie', 'Champion', 'Ultimate', 'Mega'):
    rows[stage] = {}
    for lock in ('normal', 'mega'):
        rng = random.Random(42)
        me = battle.Side(0, name='measurement', stage=stage, attribute='Free', hit_type=lock)
        foe = battle.Side(boss, name="boss", stage="Mega", attribute="Free", boss=True)
        raw = sum(battle.generate_raid(me, foe, rng=rng.random)[1] for _ in range(samples)) / samples
        mult = {'Champion': 2, 'Ultimate': 5, 'Mega': 20}.get(stage, 1)
        rows[stage][lock] = {'raw': raw, 'damage': raw * 5000 * mult}
mix = {'Mega': 2, 'Ultimate': 3, 'Champion': 3, 'Rookie': 2}
capacity = sum(rows[stage]['normal']['damage'] * count for stage, count in mix.items()) * 21
result = {'seed': 42, 'volleys_per_stage_lock': samples,
          'assumptions': 'Ideal condition; neutral attribute; no training, powers or record bonus; 21 throws/week.',
          'stages': rows, 'roster': mix, 'weekly_damage': capacity,
          'cap': 30000000, 'days_at_cap': 7 * 30000000 / capacity,
          'required_attempt_fraction': 30000000 / capacity}
(root / '_astra/raid/damage_measurements.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(json.dumps(result, indent=2))
