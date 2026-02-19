"""
Arena Battle Formula Test v3 — with Block chance from DEF.

  HP       = STR×2 + DEF×4 + LUK×2 + 50
  Base DMG = ATK_STR × (1 − DEF_DEF / (DEF_DEF + 20))
  Variance = luk_weighted_random(ATK_LUK) × max(1, ATK_STR / 3)
  Block    = DEF/(DEF+40) → dmg ×0.5                          ← NEW!
  CRIT/Lucky mutually exclusive
"""
import random
import statistics

def calc_hp(s, d, l):
    return s * 2 + d * 4 + l * 2 + 50

def calc_dmg(atk_str, def_def):
    return max(1, atk_str * (1 - def_def / (def_def + 20)))

def crit_chance(luk):
    return luk / (luk + 25)

def dodge_chance(luk):
    return luk / (luk + 30)

def lucky_chance(luk):
    return luk / (luk + 50)

def block_chance(def_stat):
    return def_stat / (def_stat + 35)

def luk_weighted_random(luk):
    luk_ratio = luk / (luk + 20)
    return random.random() * (1 - luk_ratio) + luk_ratio

def simulate_battle(a_str, a_def, a_luk, b_str, b_def, b_luk):
    a_hp = calc_hp(a_str, a_def, a_luk)
    b_hp = calc_hp(b_str, b_def, b_luk)
    a_max, b_max = a_hp, b_hp

    fighters = [
        {"name": "A", "str": a_str, "def": a_def, "luk": a_luk},
        {"name": "B", "str": b_str, "def": b_def, "luk": b_luk},
    ]

    if (a_str, a_luk, a_def) >= (b_str, b_luk, b_def):
        turn_order = [(0, 1), (1, 0)]
    else:
        turn_order = [(1, 0), (0, 1)]

    stats = {"A": {"hits": 0, "crits": 0, "luckys": 0, "dodges": 0, "blocks": 0, "total_dmg": 0},
             "B": {"hits": 0, "crits": 0, "luckys": 0, "dodges": 0, "blocks": 0, "total_dmg": 0}}

    for turn in range(1, 21):
        for atk_idx, def_idx in turn_order:
            atk = fighters[atk_idx]
            dfd = fighters[def_idx]

            if random.random() < dodge_chance(dfd["luk"]):
                stats[dfd["name"]]["dodges"] += 1
            else:
                base = calc_dmg(atk["str"], dfd["def"]) + luk_weighted_random(atk["luk"]) * max(1, atk["str"] / 3)
                is_crit = random.random() < crit_chance(atk["luk"])
                if is_crit:
                    base *= 2.5
                    stats[atk["name"]]["crits"] += 1
                else:
                    is_lucky = random.random() < lucky_chance(atk["luk"])
                    if is_lucky:
                        base *= 2
                        stats[atk["name"]]["luckys"] += 1

                # Block check
                if random.random() < block_chance(dfd["def"]):
                    base *= 0.5
                    stats[dfd["name"]]["blocks"] += 1

                dmg = max(1, int(base))
                stats[atk["name"]]["hits"] += 1
                stats[atk["name"]]["total_dmg"] += dmg

                if atk["name"] == "A":
                    b_hp -= dmg
                else:
                    a_hp -= dmg

            if b_hp <= 0:
                return "A", turn, a_hp, b_hp, a_max, b_max, stats
            if a_hp <= 0:
                return "B", turn, a_hp, b_hp, a_max, b_max, stats

    winner = "A" if a_hp >= b_hp else "B"
    return winner, 20, a_hp, b_hp, a_max, b_max, stats

def run_scenario(name, a_str, a_def, a_luk, b_str, b_def, b_luk, n=100):
    a_wins = 0
    turns_list = []
    
    for _ in range(n):
        winner, turns, *_ = simulate_battle(a_str, a_def, a_luk, b_str, b_def, b_luk)
        if winner == "A":
            a_wins += 1
        turns_list.append(turns)

    a_hp = calc_hp(a_str, a_def, a_luk)
    b_hp = calc_hp(b_str, b_def, b_luk)
    a_base_dmg = calc_dmg(a_str, b_def)
    b_base_dmg = calc_dmg(b_str, a_def)

    print(f"\n{'='*65}")
    print(f"  {name}")
    print(f"{'='*65}")
    print(f"  Player A: STR={a_str:3} DEF={a_def:3} LUK={a_luk:3}  │  HP={a_hp}")
    print(f"  Player B: STR={b_str:3} DEF={b_def:3} LUK={b_luk:3}  │  HP={b_hp}")
    print(f"  ──────────────────────────────────────────")
    print(f"  A→B  base dmg: {a_base_dmg:.1f}")
    print(f"  B→A  base dmg: {b_base_dmg:.1f}")
    print(f"  A  crit: {crit_chance(a_luk)*100:.1f}%  dodge: {dodge_chance(a_luk)*100:.1f}%  lucky: {lucky_chance(a_luk)*100:.1f}%")
    print(f"  B  crit: {crit_chance(b_luk)*100:.1f}%  dodge: {dodge_chance(b_luk)*100:.1f}%  lucky: {lucky_chance(b_luk)*100:.1f}%")
    print(f"  A  block: {block_chance(a_def)*100:.1f}%  |  B  block: {block_chance(b_def)*100:.1f}%")
    print(f"  ──────────────────────────────────────────")
    print(f"  Results ({n} battles):")
    print(f"    A wins: {a_wins}/{n} ({a_wins/n*100:.1f}%)")
    print(f"    B wins: {n-a_wins}/{n} ({(n-a_wins)/n*100:.1f}%)")
    print(f"    Avg turns: {statistics.mean(turns_list):.1f}")

    # One detailed sample
    print(f"\n  📋 Sample battle:")
    winner, turns, a_hp_end, b_hp_end, a_max, b_max, st = simulate_battle(a_str, a_def, a_luk, b_str, b_def, b_luk)
    print(f"    Winner: Player {winner} in {turns} turns")
    print(f"    A: {st['A']['hits']}hits {st['A']['crits']}crit {st['A']['luckys']}lucky | dodged {st['A']['dodges']}x blocked {st['A']['blocks']}x | dmg={st['A']['total_dmg']}")
    print(f"    B: {st['B']['hits']}hits {st['B']['crits']}crit {st['B']['luckys']}lucky | dodged {st['B']['dodges']}x blocked {st['B']['blocks']}x | dmg={st['B']['total_dmg']}")
    print(f"    Final HP: A={max(0,a_hp_end)}/{a_max}  B={max(0,b_hp_end)}/{b_max}")


if __name__ == "__main__":
    random.seed(42)
    print("⚔️  ARENA BATTLE FORMULA TEST v3 (+ Block chance)")
    print("  HP = STR×2 + DEF×4 + LUK×2 + 50")
    print("  DMG reduction = DEF / (DEF + 20)")
    print("  Block chance  = DEF / (DEF + 40) → dmg ×0.5    ← NEW!")
    print("  Random variance weighted by LUK")
    print("  CRIT/Lucky mutually exclusive")

    run_scenario("🟰 Equal Stats (all 10)", 10, 10, 10, 10, 10, 10)
    run_scenario("⚔️ STR Tank (30/10/10) vs 🛡️ DEF Tank (10/30/10)",
                 30, 10, 10,  10, 30, 10)
    run_scenario("⚔️ STR Tank (30/10/10) vs 🍀 LUK Build (10/10/30)",
                 30, 10, 10,  10, 10, 30)
    run_scenario("🛡️ DEF Tank (10/30/10) vs 🍀 LUK Build (10/10/30)",
                 10, 30, 10,  10, 10, 30)
    run_scenario("⚖️ Balanced (20/20/20) vs 💥 Glass Cannon (40/5/15)",
                 20, 20, 20,  40, 5, 15)
    run_scenario("🔥 Veteran A (25/25/20) vs 🔥 Veteran B (20/20/30)",
                 25, 25, 20,  20, 20, 30)
    run_scenario("⚔️ STR vs STR (30/10/10 vs 30/10/10)",
                 30, 10, 10,  30, 10, 10)
    run_scenario("🍀 Dodge Machine (10/10/50) vs ⚖️ Balanced (25/25/10)",
                 10, 10, 50,  25, 25, 10)

    print(f"\n{'='*65}")
    print("  DONE!")
    print(f"{'='*65}")
