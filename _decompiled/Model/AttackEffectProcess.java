/*
 * Decompiled with CFR 0.152.
 */
package Model;

import Model.Battle;
import Model.Enemy;
import Model.Enum;
import java.util.ArrayList;

public class AttackEffectProcess {
    private boolean _processed;
    private int _enemyHealthChange;
    private int _playerHealthChange;
    private Battle _battle;
    private Enum.AttackEffect _playerEffect;
    private ArrayList<Enum.AttackCondition> _playerConditions;
    private Enum.AttackEffect _enemyEffect;
    private ArrayList<Enum.AttackCondition> _enemyConditions;

    public boolean getProcessed() {
        return this._processed;
    }

    public void setProcessed(boolean p) {
        this._processed = p;
    }

    public int getEnemyHealthChange() {
        return this._enemyHealthChange;
    }

    public void setEnemyHealthChange(int change) {
        this._enemyHealthChange = change;
    }

    public int getPlayerHealthChange() {
        return this._playerHealthChange;
    }

    public void setPlayerHealthChange(int change) {
        this._playerHealthChange = change;
    }

    public Enum.AttackEffect getPlayerEffect() {
        return this._playerEffect;
    }

    public void setPlayerEffect(Enum.AttackEffect effect) {
        this._playerEffect = effect;
    }

    public Enum.AttackEffect getEnemyEffect() {
        return this._enemyEffect;
    }

    public void setEnemyEffect(Enum.AttackEffect effect) {
        this._enemyEffect = effect;
    }

    public ArrayList<Enum.AttackCondition> getPlayerConditions() {
        return this._playerConditions;
    }

    public ArrayList<Enum.AttackCondition> getEnemyConditions() {
        return this._enemyConditions;
    }

    public AttackEffectProcess(Battle battle) {
        this._battle = battle;
    }

    public boolean processAttackEffect(Enum.AttackEffect effect, Enum.AttackEffect enemyEffect, ArrayList<Enum.AttackCondition> conditions, ArrayList<Enum.AttackCondition> enemyConditions) {
        boolean isPlayer = this._battle.getPlayerFirst();
        this._playerEffect = effect;
        this._playerConditions = conditions;
        this._enemyEffect = enemyEffect;
        this._enemyConditions = enemyConditions;
        boolean disableEffect = false;
        if (isPlayer) {
            disableEffect = this.checkPlayerEffectAndConditions();
            if (!disableEffect) {
                this.checkEnemyEffectAndConditions();
            }
            this._processed = true;
        } else {
            disableEffect = this.checkEnemyEffectAndConditions();
            if (!disableEffect) {
                this.checkPlayerEffectAndConditions();
            }
            this._processed = true;
        }
        return disableEffect;
    }

    private boolean checkPlayerEffectAndConditions() {
        boolean disableEnemyEffect = false;
        if (this.checkValidConditions(true)) {
            disableEnemyEffect = this._playerEffect == Enum.AttackEffect.DisableEffect;
            this.checkSpecialConditions(true);
            this.checkEffect(true);
        }
        return disableEnemyEffect;
    }

    private boolean checkEnemyEffectAndConditions() {
        boolean disablePlayerEffect = false;
        if (this.checkValidConditions(false)) {
            disablePlayerEffect = this._enemyEffect == Enum.AttackEffect.DisableEffect;
            this.checkSpecialConditions(false);
            this.checkEffect(false);
        }
        return disablePlayerEffect;
    }

    private void checkEffect(boolean isPlayer) {
        switch (isPlayer ? this._playerEffect : this._enemyEffect) {
            case AttackUp: {
                if (isPlayer) {
                    this._battle.setAttack(this._battle.getAttack() + 1 * this.calcGreaterEffect(isPlayer));
                    break;
                }
                this._battle.setEnemyAttack(this._battle.getEnemyAttack() + 1 * this.calcGreaterEffect(isPlayer));
                break;
            }
            case DefenseUp: {
                if (!isPlayer) {
                    if (this._battle.getAttack() - 1 * this.calcGreaterEffect(isPlayer) <= 0) break;
                    this._battle.setAttack(this._battle.getAttack() - 1 * this.calcGreaterEffect(isPlayer));
                    break;
                }
                if (this._battle.getEnemyAttack() - 1 * this.calcGreaterEffect(isPlayer) <= 0) break;
                this._battle.setEnemyAttack(this._battle.getEnemyAttack() - 1 * this.calcGreaterEffect(isPlayer));
                break;
            }
            case Weaken: {
                this._battle.setAttack(1);
                this._battle.setEnemyAttack(1);
                break;
            }
            case DisableAttack: {
                if (isPlayer) {
                    this._battle.setAttack(1);
                    this._battle.setEnemyAttack(0);
                    break;
                }
                this._battle.setAttack(0);
                this._battle.setEnemyAttack(1);
                break;
            }
            case Counter: {
                if (isPlayer) {
                    this._battle.setPlayerFirst(false);
                    if (this._battle.getEnemyAttack() - 1 * this.calcGreaterEffect(isPlayer) > 0) {
                        this._battle.setEnemyAttack(this._battle.getEnemyAttack() - 1 * this.calcGreaterEffect(isPlayer));
                    }
                    this._battle.setAttack(this._battle.getAttack() + 1 * this.calcGreaterEffect(isPlayer));
                    break;
                }
                this._battle.setPlayerFirst(true);
                if (this._battle.getAttack() - 1 * this.calcGreaterEffect(isPlayer) > 0) {
                    this._battle.setAttack(this._battle.getAttack() - 1 * this.calcGreaterEffect(isPlayer));
                }
                this._battle.setEnemyAttack(this._battle.getEnemyAttack() + 1 * this.calcGreaterEffect(isPlayer));
                break;
            }
            case First: {
                if (isPlayer) {
                    this._battle.setPlayerFirst(true);
                    break;
                }
                this._battle.setPlayerFirst(false);
                break;
            }
            case Second: {
                if (isPlayer) {
                    this._battle.setPlayerFirst(false);
                    break;
                }
                this._battle.setPlayerFirst(true);
                break;
            }
            case Leech: {
                if (isPlayer && this._battle.getHealth() > 1 * this.calcGreaterEffect(isPlayer)) {
                    this._battle.setAttack(this._battle.getAttack() + 1 * this.calcGreaterEffect(isPlayer));
                    this._playerHealthChange += 1 * this.calcGreaterEffect(isPlayer);
                    break;
                }
                if (isPlayer || this._battle.getEnemyHealth() <= 1 * this.calcGreaterEffect(isPlayer)) break;
                this._battle.setEnemyAttack(this._battle.getEnemyAttack() + 1 * this.calcGreaterEffect(isPlayer));
                this._enemyHealthChange += 1 * this.calcGreaterEffect(isPlayer);
                break;
            }
            case Absorb: {
                if (isPlayer) {
                    if (this._battle.getEnemyAttack() - 1 * this.calcGreaterEffect(isPlayer) > 0) {
                        this._battle.setEnemyAttack(this._battle.getEnemyAttack() - 1 * this.calcGreaterEffect(isPlayer));
                    }
                    this._playerHealthChange += 1 * this.calcGreaterEffect(isPlayer);
                    break;
                }
                if (this._battle.getAttack() - 1 * this.calcGreaterEffect(isPlayer) > 0) {
                    this._battle.setAttack(this._battle.getAttack() - 1 * this.calcGreaterEffect(isPlayer));
                }
                this._enemyHealthChange += 1 * this.calcGreaterEffect(isPlayer);
                break;
            }
            case Heal: {
                if (isPlayer) {
                    this._battle.setAttack(0);
                    this._playerHealthChange += 1 * this.calcGreaterEffect(isPlayer);
                    break;
                }
                this._battle.setEnemyAttack(0);
                this._enemyHealthChange += 1 * this.calcGreaterEffect(isPlayer);
                break;
            }
            case ForceOppVaccine: {
                if (isPlayer) {
                    this._battle.setOppAttack(Enum.Attribute.Vaccine);
                    break;
                }
                this._battle.setAttackType(Enum.Attribute.Vaccine);
                break;
            }
            case ForceOppData: {
                if (isPlayer) {
                    this._battle.setOppAttack(Enum.Attribute.Data);
                    break;
                }
                this._battle.setAttackType(Enum.Attribute.Data);
                break;
            }
            case ForceOppVirus: {
                if (isPlayer) {
                    this._battle.setOppAttack(Enum.Attribute.Virus);
                    break;
                }
                this._battle.setAttackType(Enum.Attribute.Virus);
                break;
            }
            case PlayerIsVaccine: 
            case PlayerIsData: 
            case PlayerIsVirus: {
                Enum.Attribute att = Enum.Attribute.valueOf(isPlayer ? this._playerEffect.toString().substring(8) : this._enemyEffect.toString().substring(8));
                if (isPlayer) {
                    this._battle.setPlayerAttOverride(att);
                    break;
                }
                this._battle.setEnemyAttOverride(att);
                break;
            }
            case EnemyIsVaccine: 
            case EnemyIsData: 
            case EnemyIsVirus: {
                Enum.Attribute at = Enum.Attribute.valueOf(isPlayer ? this._playerEffect.toString().substring(7) : this._enemyEffect.toString().substring(7));
                if (!isPlayer) {
                    this._battle.setPlayerAttOverride(at);
                    break;
                }
                this._battle.setEnemyAttOverride(at);
                break;
            }
            case PlayerIsNSP: 
            case PlayerIsNS: 
            case PlayerIsDR: 
            case PlayerIsDS: 
            case PlayerIsWG: 
            case PlayerIsDA: 
            case PlayerIsNA: 
            case PlayerIsJT: 
            case PlayerIsME: 
            case PlayerIsVB: {
                Enum.Field field = this.getPlayerFieldOverrideAbbreviation(isPlayer ? this._playerEffect.toString().substring(8) : this._enemyEffect.toString().substring(8));
                if (isPlayer) {
                    this._battle.setPlayerFieldOverride(field);
                    break;
                }
                this._battle.setEnemyFieldOverride(field);
                break;
            }
            case EnemyIsNSP: 
            case EnemyIsNS: 
            case EnemyIsDR: 
            case EnemyIsDS: 
            case EnemyIsWG: 
            case EnemyIsDA: 
            case EnemyIsNA: 
            case EnemyIsJT: 
            case EnemyIsME: 
            case EnemyIsVB: {
                Enum.Field f = this.getPlayerFieldOverrideAbbreviation(isPlayer ? this._playerEffect.toString().substring(7) : this._enemyEffect.toString().substring(7));
                if (!isPlayer) {
                    this._battle.setPlayerFieldOverride(f);
                    break;
                }
                this._battle.setEnemyFieldOverride(f);
            }
        }
    }

    private void checkFirstSecond(boolean isPlayer, Enum.AttackEffect effect, ArrayList<Enum.AttackCondition> conditions) {
    }

    private int calcGreaterEffect(boolean isPlayer) {
        int effect = 1;
        effect = isPlayer ? (this._playerConditions.contains((Object)Enum.AttackCondition.EffectTimesThree) ? 3 : (this._playerConditions.contains((Object)Enum.AttackCondition.EffectTimesTwo) ? 2 : 1)) : (this._enemyConditions.contains((Object)Enum.AttackCondition.EffectTimesThree) ? 3 : (this._enemyConditions.contains((Object)Enum.AttackCondition.EffectTimesTwo) ? 2 : 1));
        return effect;
    }

    private int calcGreaterCondition(boolean isPlayer) {
        int effect = 1;
        effect = isPlayer ? (this._playerConditions.contains((Object)Enum.AttackCondition.ConditionsTimesThree) ? 3 : (this._playerConditions.contains((Object)Enum.AttackCondition.ConditionsTimesTwo) ? 2 : 1)) : (this._enemyConditions.contains((Object)Enum.AttackCondition.ConditionsTimesThree) ? 3 : (this._enemyConditions.contains((Object)Enum.AttackCondition.ConditionsTimesTwo) ? 2 : 1));
        return effect;
    }

    private void checkSpecialConditions(boolean isPlayer) {
        for (Enum.AttackCondition c : isPlayer ? this._playerConditions : this._enemyConditions) {
            switch (c) {
                case ForcePlayerSecond: {
                    if (isPlayer) {
                        this._battle.setPlayerFirst(false);
                        break;
                    }
                    this._battle.setPlayerFirst(true);
                    break;
                }
                case SacrificeAttack: {
                    if (isPlayer) {
                        this._battle.setAttack(this._battle.getAttack() - 1 * this.calcGreaterCondition(isPlayer));
                        break;
                    }
                    this._battle.setEnemyAttack(this._battle.getEnemyAttack() - 1 * this.calcGreaterCondition(isPlayer));
                    break;
                }
                case SacrificeDefense: {
                    if (!isPlayer) {
                        this._battle.setAttack(this._battle.getAttack() + 1 * this.calcGreaterCondition(isPlayer));
                        break;
                    }
                    this._battle.setEnemyAttack(this._battle.getEnemyAttack() + 1 * this.calcGreaterCondition(isPlayer));
                    break;
                }
                case SacrificeHealth: {
                    if (isPlayer) {
                        this._playerHealthChange -= 1 * this.calcGreaterCondition(isPlayer);
                        break;
                    }
                    this._enemyHealthChange -= 1 * this.calcGreaterCondition(isPlayer);
                }
            }
        }
    }

    private boolean checkValidConditions(boolean isPlayer) {
        boolean valid = false;
        for (Enum.AttackCondition c : isPlayer ? this._playerConditions : this._enemyConditions) {
            if (!this.checkCondition(c, isPlayer)) {
                valid = false;
                break;
            }
            valid = true;
        }
        return valid;
    }

    public boolean checkCondition(Enum.AttackCondition condition, boolean isPlayer) {
        boolean valid = false;
        Enemy e = this._battle.getEnemy();
        switch (condition) {
            case ForcePlayerSecond: 
            case SacrificeAttack: 
            case SacrificeDefense: 
            case SacrificeHealth: 
            case None: 
            case EffectTimesThree: 
            case EffectTimesTwo: 
            case ConditionsTimesThree: 
            case ConditionsTimesTwo: {
                valid = true;
                break;
            }
            case EnemyIsVaccine: {
                if (isPlayer) {
                    valid = this._battle.getEnemyAttOverride() == Enum.Attribute.Vaccine;
                    break;
                }
                valid = this._battle.getPlayerAttOverride() == Enum.Attribute.Vaccine;
                break;
            }
            case EnemyIsData: {
                if (isPlayer) {
                    valid = this._battle.getEnemyAttOverride() == Enum.Attribute.Data;
                    break;
                }
                valid = this._battle.getPlayerAttOverride() == Enum.Attribute.Data;
                break;
            }
            case EnemyIsVirus: {
                if (isPlayer) {
                    valid = this._battle.getEnemyAttOverride() == Enum.Attribute.Virus;
                    break;
                }
                valid = this._battle.getPlayerAttOverride() == Enum.Attribute.Virus;
                break;
            }
            case PlayerIsVaccine: {
                if (!isPlayer) {
                    valid = this._battle.getEnemyAttOverride() == Enum.Attribute.Vaccine;
                    break;
                }
                valid = this._battle.getPlayerAttOverride() == Enum.Attribute.Vaccine;
                break;
            }
            case PlayerIsData: {
                if (!isPlayer) {
                    valid = this._battle.getEnemyAttOverride() == Enum.Attribute.Data;
                    break;
                }
                valid = this._battle.getPlayerAttOverride() == Enum.Attribute.Data;
                break;
            }
            case PlayerIsVirus: {
                if (!isPlayer) {
                    valid = this._battle.getEnemyAttOverride() == Enum.Attribute.Virus;
                    break;
                }
                valid = this._battle.getPlayerAttOverride() == Enum.Attribute.Virus;
                break;
            }
            case AttackVaccine: {
                if (isPlayer) {
                    valid = this._battle.getOppAttack() == Enum.Attribute.Vaccine;
                    break;
                }
                valid = this._battle.getAttackType() == Enum.Attribute.Vaccine;
                break;
            }
            case AttackData: {
                if (isPlayer) {
                    valid = this._battle.getOppAttack() == Enum.Attribute.Data;
                    break;
                }
                valid = this._battle.getAttackType() == Enum.Attribute.Data;
                break;
            }
            case AttackVirus: {
                if (isPlayer) {
                    valid = this._battle.getOppAttack() == Enum.Attribute.Virus;
                    break;
                }
                valid = this._battle.getAttackType() == Enum.Attribute.Virus;
                break;
            }
            case VaccineWeaker: {
                if (isPlayer) {
                    valid = this._battle.getRed() < e.getOppRed();
                    break;
                }
                valid = this._battle.getRed() > e.getOppRed();
                break;
            }
            case DataWeaker: {
                if (isPlayer) {
                    valid = this._battle.getGreen() < e.getOppGreen();
                    break;
                }
                valid = this._battle.getGreen() > e.getOppGreen();
                break;
            }
            case VirusWeaker: {
                if (isPlayer) {
                    valid = this._battle.getYellow() < e.getOppYellow();
                    break;
                }
                valid = this._battle.getYellow() > e.getOppYellow();
                break;
            }
            case PlayerWeaker: {
                if (isPlayer) {
                    valid = this._battle.getRed() + this._battle.getGreen() + this._battle.getYellow() < e.getOppRed() + e.getOppGreen() + e.getOppYellow();
                    break;
                }
                valid = this._battle.getRed() + this._battle.getGreen() + this._battle.getYellow() > e.getOppRed() + e.getOppGreen() + e.getOppYellow();
                break;
            }
            case VaccineStronger: {
                if (!isPlayer) {
                    valid = this._battle.getRed() < e.getOppRed();
                    break;
                }
                valid = this._battle.getRed() > e.getOppRed();
                break;
            }
            case DataStronger: {
                if (!isPlayer) {
                    valid = this._battle.getGreen() < e.getOppGreen();
                    break;
                }
                valid = this._battle.getGreen() > e.getOppGreen();
                break;
            }
            case VirusStronger: {
                if (!isPlayer) {
                    valid = this._battle.getYellow() < e.getOppYellow();
                    break;
                }
                valid = this._battle.getYellow() > e.getOppYellow();
                break;
            }
            case PlayerStronger: {
                if (!isPlayer) {
                    valid = this._battle.getRed() + this._battle.getGreen() + this._battle.getYellow() < e.getOppRed() + e.getOppGreen() + e.getOppYellow();
                    break;
                }
                valid = this._battle.getRed() + this._battle.getGreen() + this._battle.getYellow() > e.getOppRed() + e.getOppGreen() + e.getOppYellow();
                break;
            }
            case EnemyIsNSP: {
                if (isPlayer) {
                    valid = this._battle.getEnemyFieldOverride() == Enum.Field.NatureSpirit;
                    break;
                }
                valid = this._battle.getPlayerFieldOverride() == Enum.Field.NatureSpirit;
                break;
            }
            case EnemyIsNS: {
                if (isPlayer) {
                    valid = this._battle.getEnemyFieldOverride() == Enum.Field.NightmareSoldier;
                    break;
                }
                valid = this._battle.getPlayerFieldOverride() == Enum.Field.NightmareSoldier;
                break;
            }
            case EnemyIsDR: {
                if (isPlayer) {
                    valid = this._battle.getEnemyFieldOverride() == Enum.Field.DragonsRoar;
                    break;
                }
                valid = this._battle.getPlayerFieldOverride() == Enum.Field.DragonsRoar;
                break;
            }
            case EnemyIsDS: {
                if (isPlayer) {
                    valid = this._battle.getEnemyFieldOverride() == Enum.Field.DeepSaver;
                    break;
                }
                valid = this._battle.getPlayerFieldOverride() == Enum.Field.DeepSaver;
                break;
            }
            case EnemyIsWG: {
                if (isPlayer) {
                    valid = this._battle.getEnemyFieldOverride() == Enum.Field.WindGuardian;
                    break;
                }
                valid = this._battle.getPlayerFieldOverride() == Enum.Field.WindGuardian;
                break;
            }
            case EnemyIsDA: {
                if (isPlayer) {
                    valid = this._battle.getEnemyFieldOverride() == Enum.Field.DarkArea;
                    break;
                }
                valid = this._battle.getPlayerFieldOverride() == Enum.Field.DarkArea;
                break;
            }
            case EnemyIsNA: {
                if (isPlayer) {
                    valid = this._battle.getEnemyFieldOverride() == Enum.Field.NA;
                    break;
                }
                valid = this._battle.getPlayerFieldOverride() == Enum.Field.NA;
                break;
            }
            case EnemyIsJT: {
                if (isPlayer) {
                    valid = this._battle.getEnemyFieldOverride() == Enum.Field.JungleTrooper;
                    break;
                }
                valid = this._battle.getPlayerFieldOverride() == Enum.Field.JungleTrooper;
                break;
            }
            case EnemyIsME: {
                if (isPlayer) {
                    valid = this._battle.getEnemyFieldOverride() == Enum.Field.MetalEmpire;
                    break;
                }
                valid = this._battle.getPlayerFieldOverride() == Enum.Field.MetalEmpire;
                break;
            }
            case EnemyIsVB: {
                if (isPlayer) {
                    valid = this._battle.getEnemyFieldOverride() == Enum.Field.VirusBuster;
                    break;
                }
                valid = this._battle.getPlayerFieldOverride() == Enum.Field.VirusBuster;
                break;
            }
            case PlayerIsNSP: {
                if (!isPlayer) {
                    valid = this._battle.getPlayerFieldOverride() == Enum.Field.NatureSpirit;
                    break;
                }
                valid = this._battle.getPlayerFieldOverride() == Enum.Field.NatureSpirit;
                break;
            }
            case PlayerIsNS: {
                if (!isPlayer) {
                    valid = this._battle.getPlayerFieldOverride() == Enum.Field.NightmareSoldier;
                    break;
                }
                valid = this._battle.getPlayerFieldOverride() == Enum.Field.NightmareSoldier;
                break;
            }
            case PlayerIsDR: {
                if (!isPlayer) {
                    valid = this._battle.getPlayerFieldOverride() == Enum.Field.DragonsRoar;
                    break;
                }
                valid = this._battle.getPlayerFieldOverride() == Enum.Field.DragonsRoar;
                break;
            }
            case PlayerIsDS: {
                if (!isPlayer) {
                    valid = this._battle.getPlayerFieldOverride() == Enum.Field.DeepSaver;
                    break;
                }
                valid = this._battle.getPlayerFieldOverride() == Enum.Field.DeepSaver;
                break;
            }
            case PlayerIsWG: {
                if (!isPlayer) {
                    valid = this._battle.getPlayerFieldOverride() == Enum.Field.WindGuardian;
                    break;
                }
                valid = this._battle.getPlayerFieldOverride() == Enum.Field.WindGuardian;
                break;
            }
            case PlayerIsDA: {
                if (!isPlayer) {
                    valid = this._battle.getPlayerFieldOverride() == Enum.Field.DarkArea;
                    break;
                }
                valid = this._battle.getPlayerFieldOverride() == Enum.Field.DarkArea;
                break;
            }
            case PlayerIsNA: {
                if (!isPlayer) {
                    valid = this._battle.getPlayerFieldOverride() == Enum.Field.NA;
                    break;
                }
                valid = this._battle.getPlayerFieldOverride() == Enum.Field.NA;
                break;
            }
            case PlayerIsJT: {
                if (!isPlayer) {
                    valid = this._battle.getPlayerFieldOverride() == Enum.Field.JungleTrooper;
                    break;
                }
                valid = this._battle.getPlayerFieldOverride() == Enum.Field.JungleTrooper;
                break;
            }
            case PlayerIsME: {
                if (!isPlayer) {
                    valid = this._battle.getPlayerFieldOverride() == Enum.Field.MetalEmpire;
                    break;
                }
                valid = this._battle.getPlayerFieldOverride() == Enum.Field.MetalEmpire;
                break;
            }
            case PlayerIsVB: {
                if (!isPlayer) {
                    valid = this._battle.getEnemyFieldOverride() == Enum.Field.VirusBuster;
                    break;
                }
                valid = this._battle.getPlayerFieldOverride() == Enum.Field.VirusBuster;
                break;
            }
            case PlayerFirst: {
                if (isPlayer) {
                    valid = this._battle.getPlayerFirst();
                    break;
                }
                valid = !this._battle.getPlayerFirst();
                break;
            }
            case PlayerSecond: {
                if (!isPlayer) {
                    valid = this._battle.getPlayerFirst();
                    break;
                }
                valid = !this._battle.getPlayerFirst();
                break;
            }
            case LowerPlayerHealth: {
                if (isPlayer) {
                    valid = this._battle.getHealth() + this._playerHealthChange < this._battle.getEnemyHealth() + this._enemyHealthChange;
                    break;
                }
                valid = this._battle.getHealth() + this._playerHealthChange > this._battle.getEnemyHealth() + this._enemyHealthChange;
                break;
            }
            case HigherPlayerHealth: {
                if (!isPlayer) {
                    valid = this._battle.getHealth() + this._playerHealthChange < this._battle.getEnemyAttack() + this._enemyHealthChange;
                    break;
                }
                valid = this._battle.getHealth() + this._playerHealthChange > this._battle.getEnemyAttack() + this._enemyHealthChange;
                break;
            }
            case HalfPlayerHealth: {
                if (isPlayer) {
                    valid = this._battle.getHealth() + this._playerHealthChange <= this._battle.getFullHealth() / 2;
                    break;
                }
                valid = this._battle.getEnemyHealth() + this._enemyHealthChange <= e.getEnemyHealth() / 2;
                break;
            }
            case HalfOppHealth: {
                valid = !isPlayer ? this._battle.getHealth() + this._playerHealthChange <= this._battle.getFullHealth() / 2 : this._battle.getEnemyHealth() + this._enemyHealthChange <= e.getEnemyHealth() / 2;
            }
        }
        return valid;
    }

    public String getAttackDescription(double scale, String name, Enum.AttackEffect effect, ArrayList<Enum.AttackCondition> conditions) {
        String desc = this.getEffectDescription(effect) + (conditions.isEmpty() ? "" : " " + this.getConditionDescription(conditions.get(0)));
        for (int i = 1; i < conditions.size(); ++i) {
            if (this.getConditionDescription(conditions.get(i)).length() == 0) continue;
            desc = desc + " and " + this.getConditionDescription(conditions.get(i));
        }
        return this.styleAttackDescription(scale, name, desc);
    }

    private String styleAttackDescription(double scale, String name, String desc) {
        double width = 80.0 * scale;
        double nameWidth = 44.0 * scale;
        double margin = 1.0 * scale;
        String[] part = name.split(" ");
        if (part.length > 2 && part[0].length() + part[1].length() + 1 <= 14) {
            part[0] = part[0] + " " + part[1];
            part[1] = part[2];
        } else if (part.length > 2 && part[1].length() + part[2].length() + 1 <= 20) {
            part[1] = part[1] + " " + part[2];
        }
        String attack = "<html><div style=\"width:" + width + "px\"><p style=\"padding:0px;text-align:center;font-weight:bold;margin-bottom:" + margin + "px;\">" + (part.length > 1 ? part[0] + "<br>" + part[1] : part[0]) + "</p><p>" + desc + "</p></div></html>";
        return attack;
    }

    private String getEffectDescription(Enum.AttackEffect effect) {
        String desc = "";
        switch (effect) {
            case None: {
                desc = "Basic attack";
                break;
            }
            case AttackUp: {
                desc = "Attack up";
                break;
            }
            case DefenseUp: {
                desc = "Defense up";
                break;
            }
            case Weaken: {
                desc = "Weakens all attacks";
                break;
            }
            case DisableAttack: {
                desc = "Enemy does no damage";
                break;
            }
            case DisableEffect: {
                desc = "Disables enemy's effects";
                break;
            }
            case Counter: {
                desc = "Counters";
                break;
            }
            case First: {
                desc = "Moves first";
                break;
            }
            case Second: {
                desc = "Moves second";
                break;
            }
            case Leech: {
                desc = "Leeches health";
                break;
            }
            case Absorb: {
                desc = "Absorbs damage";
                break;
            }
            case Heal: {
                desc = "Heals";
                break;
            }
            case ForceOppVaccine: {
                desc = "Forces vaccine attack";
                break;
            }
            case ForceOppData: {
                desc = "Forces data attack";
                break;
            }
            case ForceOppVirus: {
                desc = "Forces virus attack";
                break;
            }
            case PlayerIsVaccine: 
            case PlayerIsData: 
            case PlayerIsVirus: {
                desc = "Digimon becomes " + effect.toString().substring(8).toLowerCase();
                break;
            }
            case EnemyIsVaccine: 
            case EnemyIsData: 
            case EnemyIsVirus: {
                desc = "Enemy becomes " + effect.toString().substring(7).toLowerCase();
                break;
            }
            case PlayerIsNSP: 
            case PlayerIsNS: 
            case PlayerIsDR: 
            case PlayerIsDS: 
            case PlayerIsWG: 
            case PlayerIsDA: 
            case PlayerIsNA: 
            case PlayerIsJT: 
            case PlayerIsME: 
            case PlayerIsVB: {
                desc = "Digimon becomes " + effect.toString().substring(8);
                break;
            }
            case EnemyIsNSP: 
            case EnemyIsNS: 
            case EnemyIsDR: 
            case EnemyIsDS: 
            case EnemyIsWG: 
            case EnemyIsDA: 
            case EnemyIsNA: 
            case EnemyIsJT: 
            case EnemyIsME: 
            case EnemyIsVB: {
                desc = "Enemy becomes " + effect.toString().substring(7);
                break;
            }
            default: {
                throw new AssertionError((Object)effect.name());
            }
        }
        return desc;
    }

    private String getConditionDescription(Enum.AttackCondition condition) {
        String desc = "";
        switch (condition) {
            case None: {
                break;
            }
            case AttackVaccine: {
                desc = "if enemy uses vaccine";
                break;
            }
            case AttackData: {
                desc = "if enemy uses data";
                break;
            }
            case AttackVirus: {
                desc = "if enemy uses virus";
                break;
            }
            case PlayerIsVaccine: 
            case PlayerIsData: 
            case PlayerIsVirus: {
                desc = "if Digimon is " + condition.toString().substring(8).toLowerCase();
                break;
            }
            case EnemyIsVaccine: 
            case EnemyIsData: 
            case EnemyIsVirus: {
                desc = "if enemy is " + condition.toString().substring(7).toLowerCase();
                break;
            }
            case VaccineWeaker: {
                desc = "if Digimon's vaccine is weaker";
                break;
            }
            case DataWeaker: {
                desc = "if Digimon's data is weaker";
                break;
            }
            case VirusWeaker: {
                desc = "if Digimon's virus is weaker";
                break;
            }
            case PlayerWeaker: {
                desc = "if Digimon is weaker";
                break;
            }
            case VaccineStronger: {
                desc = "if Digimon's vaccine is stronger";
                break;
            }
            case DataStronger: {
                desc = "if Digimon's data is stronger";
                break;
            }
            case VirusStronger: {
                desc = "if Digimon's virus is stronger";
                break;
            }
            case PlayerStronger: {
                desc = "if Digimon is stronger";
                break;
            }
            case PlayerIsNSP: 
            case PlayerIsNS: 
            case PlayerIsDR: 
            case PlayerIsDS: 
            case PlayerIsWG: 
            case PlayerIsDA: 
            case PlayerIsNA: 
            case PlayerIsJT: 
            case PlayerIsME: 
            case PlayerIsVB: {
                desc = "if Digimon is " + condition.toString().substring(8);
                break;
            }
            case EnemyIsNSP: 
            case EnemyIsNS: 
            case EnemyIsDR: 
            case EnemyIsDS: 
            case EnemyIsWG: 
            case EnemyIsDA: 
            case EnemyIsNA: 
            case EnemyIsJT: 
            case EnemyIsME: 
            case EnemyIsVB: {
                desc = "if enemy is " + condition.toString().substring(7);
                break;
            }
            case ForcePlayerSecond: {
                desc = "and Digimon attacks last";
                break;
            }
            case PlayerFirst: {
                desc = "if Digimon attacks first";
                break;
            }
            case PlayerSecond: {
                desc = "if Digimon attacks last";
                break;
            }
            case SacrificeAttack: {
                desc = "at the expense of attack";
                break;
            }
            case SacrificeDefense: {
                desc = "at the expense of defense";
                break;
            }
            case SacrificeHealth: {
                desc = "and Digimon loses health";
                break;
            }
            case LowerPlayerHealth: {
                desc = "if Digimon's health is lower";
                break;
            }
            case HigherPlayerHealth: {
                desc = "if Digimon's health is higher";
                break;
            }
            case HalfPlayerHealth: {
                desc = "if Digimon's health is 50% or less";
                break;
            }
            case HalfOppHealth: {
                desc = "if enemy's health is 50% or less";
                break;
            }
            case EffectTimesTwo: {
                break;
            }
            case EffectTimesThree: {
                break;
            }
            case ConditionsTimesTwo: {
                break;
            }
            case ConditionsTimesThree: {
                break;
            }
            default: {
                throw new AssertionError((Object)condition.name());
            }
        }
        return desc;
    }

    public String test(int scale, String name) {
        ArrayList<Enum.AttackCondition> conditions = new ArrayList<Enum.AttackCondition>();
        conditions.add(Enum.AttackCondition.HalfPlayerHealth);
        return this.getAttackDescription(scale, name, Enum.AttackEffect.DisableEffect, conditions);
    }

    private Enum.Field getPlayerFieldOverrideAbbreviation(String field) {
        Enum.Field valid = Enum.Field.None;
        switch (field) {
            case "NSP": {
                valid = Enum.Field.NatureSpirit;
                break;
            }
            case "NS": {
                valid = Enum.Field.NightmareSoldier;
                break;
            }
            case "DR": {
                valid = Enum.Field.DragonsRoar;
                break;
            }
            case "DS": {
                valid = Enum.Field.DeepSaver;
                break;
            }
            case "WG": {
                valid = Enum.Field.WindGuardian;
                break;
            }
            case "DA": {
                valid = Enum.Field.DarkArea;
                break;
            }
            case "NA": {
                valid = Enum.Field.NA;
                break;
            }
            case "JT": {
                valid = Enum.Field.JungleTrooper;
                break;
            }
            case "ME": {
                valid = Enum.Field.MetalEmpire;
                break;
            }
            case "VB": {
                valid = Enum.Field.VirusBuster;
            }
        }
        return valid;
    }
}

