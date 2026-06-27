/*
 * Decompiled with CFR 0.152.
 */
package Model;

import Controller.Utility;
import Model.AttackEffectProcess;
import Model.Config;
import Model.ConsumableDrops;
import Model.Enemy;
import Model.Enum;
import Model.EvolutionInfo;
import Model.FoodType;
import Model.Item;
import Model.PhysicalState;
import Model.WorldMap;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Iterator;
import java.util.Map;
import java.util.Random;

public class Battle {
    private ArrayList<String> _battleRecord = new ArrayList();
    private AttackEffectProcess _process = new AttackEffectProcess(this);
    private boolean _enemySurrender;
    private BattleType _battleType;
    private PhysicalState _digimon;
    private boolean _inProgress;
    private boolean _playerFirst;
    private int _oppDifficulty = 1;
    private int _attackRed;
    private int _attackGreen;
    private int _attackYellow;
    private int _fullHealth;
    private int _health;
    private Enum.Attribute _attribute;
    private Enum.Element _element;
    private Enum.Field _field;
    private int _digimonIndex;
    private int _enemyAttack;
    private int _previousEnemyAttack;
    private Enum.Attribute _previousEnemyAttackType = Enum.Attribute.None;
    private Enum.Attribute _zeroEnemyAttack = Enum.Attribute.None;
    private int _attack;
    private int _previousAttack;
    private Enum.Attribute _previousAttackType = Enum.Attribute.None;
    private Enum.Attribute _zeroAttack = Enum.Attribute.None;
    private Enemy _enemy;
    private int _enemyHealth;
    private ConsumableDrops _item = null;
    private int _bitsWon;
    private int _selfBonus;
    private int _oppBonus;
    private Enum.Attribute _attackType = Enum.Attribute.None;
    private Enum.Attribute _oppAttack = Enum.Attribute.None;
    private Enum.AIType _playerAI = Enum.AIType.Random;
    private boolean _enemyIsSick = false;
    private Enum.Attribute _playerAttOverride;
    private Enum.Attribute _enemyAttOverride;
    private Enum.Field _playerFieldOverride;
    private Enum.Field _enemyFieldOverride;
    private Enum.Element _playerElementOverride;
    private Enum.Element _enemyElementOverride;

    public ArrayList<String> getBattleRecord() {
        return this._battleRecord;
    }

    public AttackEffectProcess getProcess() {
        return this._process;
    }

    public ConsumableDrops getItem() {
        return this._item;
    }

    public int getBitsWon() {
        return this._bitsWon;
    }

    public void setOppDifficulty(int i) {
        this._oppDifficulty = i;
    }

    public BattleType getBattleType() {
        return this._battleType;
    }

    public Enemy getEnemy() {
        return this._enemy;
    }

    public boolean getEnemySurrender() {
        return this._enemySurrender;
    }

    public void setEnemySurrender(boolean newSurrender) {
        this._enemySurrender = newSurrender;
    }

    public boolean getInProgress() {
        return this._inProgress;
    }

    public void setInProgress(boolean newProgress) {
        this._inProgress = newProgress;
    }

    public boolean getPlayerFirst() {
        return this._playerFirst;
    }

    public void setPlayerFirst(boolean newFirst) {
        this._playerFirst = newFirst;
    }

    public int getSelfBonus() {
        return this._selfBonus;
    }

    public int getOppBonus() {
        return this._oppBonus;
    }

    public int getRed() {
        return this._attackRed;
    }

    public int getGreen() {
        return this._attackGreen;
    }

    public int getYellow() {
        return this._attackYellow;
    }

    public void setOppAttack(Enum.Attribute newAtt) {
        this._oppAttack = newAtt;
    }

    public Enum.Attribute getOppAttack() {
        return this._oppAttack;
    }

    public int getEnemyHealth() {
        return this._enemyHealth;
    }

    public void setEnemyHealth(int newHealth) {
        this._enemyHealth = newHealth;
    }

    public void setAttackType(Enum.Attribute att) {
        this._attackType = att;
    }

    public Enum.Attribute getAttackType() {
        return this._attackType;
    }

    public int getAttack() {
        return this._attack;
    }

    public void setAttack(int attack) {
        if (attack == 0) {
            this._previousAttack = this._attack;
            this._previousAttackType = this._attackType;
        }
        this._attack = attack;
    }

    public int getEnemyAttack() {
        return this._enemyAttack;
    }

    public void setEnemyAttack(int attack) {
        if (attack == 0) {
            this._previousEnemyAttack = this._enemyAttack;
            this._previousEnemyAttackType = this._oppAttack;
        }
        this._enemyAttack = attack;
    }

    public int getHealth() {
        return this._health;
    }

    public void setHealth(int newHealth) {
        this._health = newHealth;
    }

    public int getFullHealth() {
        return this._fullHealth;
    }

    public Enum.Field getField() {
        return this._field;
    }

    public Enum.Attribute getAttribute() {
        return this._attribute;
    }

    public void setPlayerAttOverride(Enum.Attribute att) {
        this._playerAttOverride = att;
    }

    public Enum.Attribute getPlayerAttOverride() {
        return this._playerAttOverride;
    }

    public void setEnemyAttOverride(Enum.Attribute att) {
        this._enemyAttOverride = att;
    }

    public Enum.Attribute getEnemyAttOverride() {
        return this._enemyAttOverride;
    }

    public void setPlayerFieldOverride(Enum.Field field) {
        this._playerFieldOverride = field;
    }

    public Enum.Field getPlayerFieldOverride() {
        return this._playerFieldOverride;
    }

    public void setEnemyFieldOverride(Enum.Field field) {
        this._enemyFieldOverride = field;
    }

    public Enum.Field getEnemyFieldOverride() {
        return this._enemyFieldOverride;
    }

    public Battle(Enemy npc1, Enemy npc2, PhysicalState digimon) {
        this._battleRecord.add("***NEW BATTLE***");
        this._digimon = digimon;
        this._attackRed = npc1.getOppRed();
        this._attackGreen = npc1.getOppGreen();
        this._attackYellow = npc1.getOppYellow();
        this._health = npc1.getEnemyHealth();
        this._fullHealth = npc1.getEnemyHealth();
        this._attribute = npc1.getOppAttribute();
        this._field = npc1.getOppField();
        this._element = npc1.getOppElement();
        this._digimonIndex = npc1.getIndex();
        this._playerAI = npc1.getAI() != null ? npc1.getAI() : this.randomizeAI(false);
        this._enemyHealth = npc2.getEnemyHealth();
        this._enemy = npc2;
        this._enemy.setAI(npc2.getAI() != null ? npc2.getAI() : this.randomizeAI(false));
    }

    public Battle(PhysicalState digimon, BattleType battleType, Enemy enemy) {
        this._battleRecord.add("***NEW BATTLE***");
        this._battleType = battleType;
        this._digimon = digimon;
        this.setupOpponents(enemy);
        if (this._digimon.getWins() >= Config._randomAIWins && this._digimon.getWins() < Config._bruteAIWins) {
            this._playerAI = Enum.AIType.Random;
        } else if (this._digimon.getWins() >= Config._bruteAIWins && this._digimon.getWins() < Config._strategicBruteAIWins) {
            this._playerAI = Enum.AIType.Brute;
        } else if (this._digimon.getWins() >= Config._strategicBruteAIWins && this._digimon.getWins() < Config._strategicDefenseAIWins) {
            this._playerAI = Enum.AIType.StrategicBrute;
        } else if (this._digimon.getWins() >= Config._strategicDefenseAIWins && this._digimon.getWins() < Config._strategicBalancedAIWins) {
            this._playerAI = Enum.AIType.StrategicDefense;
        } else if (this._digimon.getWins() >= Config._strategicBalancedAIWins) {
            this._playerAI = this._enemy.getOppRed() + this._enemy.getOppYellow() + this._enemy.getOppGreen() + this._enemyHealth > this._attackRed + this._attackYellow + this._attackGreen + this._health ? Enum.AIType.StrategicDefense : Enum.AIType.StrategicBalanced;
        }
        this._inProgress = true;
    }

    private void calcBonus(Enum.Field field, Enum.Field oppField, Enum.Element element, Enum.Element oppElement) {
        this._selfBonus = this.calcAffinityBonus(field, oppField, element, oppElement);
        this._oppBonus = this.calcAffinityBonus(oppField, field, oppElement, element);
    }

    private int calcAffinityBonus(Enum.Field field, Enum.Field oppField, Enum.Element element, Enum.Element oppElement) {
        Map<Enum.Field, Map<Enum.Field, Integer>> fields = this._digimon.getAffinity().getFields();
        Map<Enum.Element, Map<Enum.Element, Integer>> elements = this._digimon.getAffinity().getElements();
        return fields.get((Object)field).get((Object)oppField) + elements.get((Object)element).get((Object)oppElement);
    }

    public void checkFirst(boolean skipPlayer) {
        this._playerFirst = false;
        Random random = new Random();
        int r1 = random.nextInt(2);
        if (this._battleType != BattleType.PvP) {
            this.enemyAttackChoose();
        }
        if (!skipPlayer) {
            double playerSpeed = (double)(this._attackRed + this._attackYellow + this._attackGreen) * ((double)this._health / (double)this._fullHealth);
            double oppSpeed = (double)(this._enemy.getOppRed() + this._enemy.getOppYellow() + this._enemy.getOppGreen()) * ((double)this._enemyHealth / (double)this._enemy.getEnemyHealth());
            this._playerFirst = playerSpeed > oppSpeed ? true : (playerSpeed < oppSpeed ? false : r1 == 0);
        }
    }

    public void attack() {
        if (!this._process.getProcessed()) {
            this._attack = this.getBaseAttack(this._digimon.getGrowthStage()) + this.calcAttackPower(this._attackType, true);
            this._enemyAttack = this.getBaseAttack(this._enemy.getOppStage()) + this.calcAttackPower(this._oppAttack, false);
            this.processAttack();
        }
    }

    public void processState() {
        if (this._playerFirst) {
            if (this._process.getPlayerEffect() == Enum.AttackEffect.Heal) {
                this._digimon.setCurrentState(Enum.State.PlayerHealing);
            } else {
                this._digimon.setCurrentState(Enum.State.Battling_PlayerAttack);
            }
        } else if (this._process.getEnemyEffect() == Enum.AttackEffect.Heal) {
            this._digimon.setCurrentState(Enum.State.EnemyHealing);
        } else {
            this._digimon.setCurrentState(Enum.State.Battling_OpponentAttack);
        }
    }

    private void processAttack() {
        this._playerAttOverride = this._attribute;
        this._enemyAttOverride = this._enemy.getOppAttribute();
        this._playerFieldOverride = this._field;
        this._enemyFieldOverride = this._enemy.getOppField();
        this._playerElementOverride = this._element;
        this._enemyElementOverride = this._enemy.getOppElement();
        Enum.AttackEffect effect = Enum.AttackEffect.None;
        ArrayList<Enum.AttackCondition> conditions = new ArrayList<Enum.AttackCondition>();
        Enum.AttackEffect enemyEffect = Enum.AttackEffect.None;
        ArrayList<Enum.AttackCondition> enemyConditions = new ArrayList();
        EvolutionInfo info = this._enemy.getIndex() == -1 ? new EvolutionInfo() : this._digimon.getEvolution().getDigimon(this._enemy.getIndex());
        switch (this._oppAttack) {
            case Vaccine: {
                enemyEffect = info.getVaccineEffect();
                enemyConditions = info.getVaccineConditions();
                break;
            }
            case Data: {
                enemyEffect = info.getDataEffect();
                enemyConditions = info.getDataConditions();
                break;
            }
            case Virus: {
                enemyEffect = info.getVirusEffect();
                enemyConditions = info.getVirusConditions();
            }
        }
        info = this._digimon.getEvolution().getDigimon(this._digimonIndex);
        switch (this._attackType) {
            case Vaccine: {
                effect = info.getVaccineEffect();
                conditions = info.getVaccineConditions();
                break;
            }
            case Data: {
                effect = info.getDataEffect();
                conditions = info.getDataConditions();
                break;
            }
            case Virus: {
                effect = info.getVirusEffect();
                conditions = info.getVirusConditions();
            }
        }
        this._process.processAttackEffect(effect, enemyEffect, conditions, enemyConditions);
        this.calcBonus(this._playerFieldOverride, this._enemyFieldOverride, this._playerElementOverride, this._enemyElementOverride);
        this._attack = this._attack > 0 ? (this._attack += this._selfBonus) : 0;
        this._enemyAttack = this._enemyAttack > 0 ? (this._enemyAttack += this._oppBonus) : 0;
        if (this._oppAttack == Enum.Attribute.None) {
            this._enemyAttack = 0;
        }
        if (this._attackType == Enum.Attribute.None) {
            this._attack = 0;
        }
    }

    public void finishAttack(int health, boolean isEnemy) {
        String s = "";
        String name = this._digimon.getEvolution().getDigimon(this._digimonIndex).getName();
        String enemyName = this._digimon.getEvolution().getDigimon(this._enemy.getIndex()).getName();
        if (isEnemy) {
            this._battleRecord.add(name + " (P) deals " + this._attack + " damage to " + enemyName + " (O) with " + (Object)((Object)this._attackType) + " attack");
            s = enemyName + " (O) HP: " + this._enemyHealth + " -> ";
            this._enemyHealth = health -= this._attack;
            s = s + this._enemyHealth;
        } else {
            this._battleRecord.add(enemyName + " (O) deals " + this._enemyAttack + " damage to " + name + " (P) with " + (Object)((Object)this._oppAttack) + " attack");
            s = name + " (P) HP: " + this._health + " -> ";
            this._health = health -= this._enemyAttack;
            s = s + this._health;
        }
        this._battleRecord.add(s);
        this._battleRecord.add("");
        this.checkRememberZeroAttack(isEnemy);
    }

    private void checkRememberZeroAttack(boolean isPlayer) {
        Random r = new Random();
        int i = r.nextInt(5 + (isPlayer ? (this._playerAI == Enum.AIType.Brute ? -3 : 0) : (this._enemy.getAI() == Enum.AIType.Brute ? -3 : 0)));
        if (isPlayer && this._zeroAttack != Enum.Attribute.None && i == 0) {
            this._zeroAttack = Enum.Attribute.None;
        }
        if (!isPlayer && this._zeroEnemyAttack != Enum.Attribute.None && i == 1) {
            this._zeroEnemyAttack = Enum.Attribute.None;
        }
        if ((this._attack == 0 || this._attack == 1 && this._process.getEnemyEffect() == Enum.AttackEffect.Weaken) && this._playerAI != Enum.AIType.Random) {
            this._zeroAttack = this._attackType;
        }
        if ((this._enemyAttack == 0 || this._enemyAttack == 1 && this._process.getPlayerEffect() == Enum.AttackEffect.Weaken) && this._enemy.getAI() != Enum.AIType.Random) {
            this._zeroEnemyAttack = this._oppAttack;
        }
    }

    private int calcAttackPower(Enum.Attribute attackType, boolean isEnemy) {
        int attackPower = 0;
        switch (attackType) {
            case Vaccine: {
                if (this._attackRed < this._enemy.getOppRed()) {
                    if (isEnemy) {
                        --attackPower;
                        break;
                    }
                    ++attackPower;
                    break;
                }
                if (this._attackRed <= this._enemy.getOppRed()) break;
                if (isEnemy) {
                    ++attackPower;
                    break;
                }
                --attackPower;
                break;
            }
            case Data: {
                if (this._attackGreen < this._enemy.getOppGreen()) {
                    if (isEnemy) {
                        --attackPower;
                        break;
                    }
                    ++attackPower;
                    break;
                }
                if (this._attackGreen <= this._enemy.getOppGreen()) break;
                if (isEnemy) {
                    ++attackPower;
                    break;
                }
                --attackPower;
                break;
            }
            case Virus: {
                if (this._attackYellow < this._enemy.getOppYellow()) {
                    if (isEnemy) {
                        --attackPower;
                        break;
                    }
                    ++attackPower;
                    break;
                }
                if (this._attackYellow <= this._enemy.getOppYellow()) break;
                if (isEnemy) {
                    ++attackPower;
                    break;
                }
                --attackPower;
            }
        }
        return attackPower;
    }

    public void playerAttackChoose() {
        switch (this._playerAI) {
            case Random: {
                this._attackType = this.randomAI(true);
                break;
            }
            case Brute: {
                this._attackType = this.bruteAI(this._attribute, this._attackRed, this._attackGreen, this._attackYellow, true);
                break;
            }
            case StrategicBalanced: 
            case StrategicBrute: 
            case StrategicDefense: {
                this._attackType = this.strategicAI(this._playerAI, this._attribute, this._attackRed, this._attackGreen, this._attackYellow, true);
            }
        }
        if (this._attackType == Enum.Attribute.None) {
            this._attackType = this._attribute;
            if (this._attackType == Enum.Attribute.None) {
                if (this._attackRed > 0) {
                    this._attackType = Enum.Attribute.Vaccine;
                } else if (this._attackGreen > 0) {
                    this._attackType = Enum.Attribute.Data;
                } else if (this._attackYellow > 0) {
                    this._attackType = Enum.Attribute.Virus;
                }
            }
        }
    }

    public void enemyAttackChoose() {
        switch (this._enemy.getAI()) {
            case Random: {
                this._oppAttack = this.randomAI(false);
                break;
            }
            case Brute: {
                this._oppAttack = this.bruteAI(this._enemy.getOppAttribute(), this._enemy.getOppRed(), this._enemy.getOppGreen(), this._enemy.getOppYellow(), false);
                break;
            }
            case StrategicBalanced: 
            case StrategicBrute: 
            case StrategicDefense: {
                this._oppAttack = this.strategicAI(this._enemy.getAI(), this._enemy.getOppAttribute(), this._enemy.getOppRed(), this._enemy.getOppGreen(), this._enemy.getOppYellow(), false);
            }
        }
        if (this._oppAttack == Enum.Attribute.None) {
            this._oppAttack = this._enemy.getOppAttribute();
            if (this._oppAttack == Enum.Attribute.None) {
                if (this._enemy.getOppRed() > 0) {
                    this._oppAttack = Enum.Attribute.Vaccine;
                } else if (this._enemy.getOppGreen() > 0) {
                    this._oppAttack = Enum.Attribute.Data;
                } else if (this._enemy.getOppYellow() > 0) {
                    this._oppAttack = Enum.Attribute.Virus;
                }
            }
        }
    }

    private Enum.Attribute strategicAI(Enum.AIType ai, Enum.Attribute attribute, int red, int green, int yellow, boolean isPlayer) {
        Enum.Attribute attack = attribute;
        int vaccineTotal = 0;
        int dataTotal = 0;
        int virusTotal = 0;
        int vaccinePower = this.calcAttackPower(Enum.Attribute.Vaccine, isPlayer);
        int dataPower = this.calcAttackPower(Enum.Attribute.Data, isPlayer);
        int virusPower = this.calcAttackPower(Enum.Attribute.Virus, isPlayer);
        vaccineTotal = vaccinePower;
        dataTotal = dataPower;
        virusTotal = virusPower;
        EvolutionInfo digimon = this._digimon.getEvolution().getDigimon(!isPlayer ? this._enemy.getIndex() : this._digimonIndex);
        EvolutionInfo enemy = isPlayer && this._enemy.getIndex() == -1 ? new EvolutionInfo() : this._digimon.getEvolution().getDigimon(isPlayer ? this._enemy.getIndex() : this._digimonIndex);
        switch (ai) {
            case StrategicBalanced: {
                attack = this.evenStrategy(isPlayer, digimon, enemy, vaccineTotal, dataTotal, virusTotal);
                break;
            }
            case StrategicBrute: {
                attack = this.bruteStrategy(isPlayer, digimon, enemy, vaccineTotal, dataTotal, virusTotal);
                break;
            }
            case StrategicDefense: {
                attack = this.defenseStrategy(isPlayer, digimon, enemy, vaccineTotal, dataTotal, virusTotal);
            }
        }
        return attack;
    }

    private Enum.Attribute evenStrategy(boolean isPlayer, EvolutionInfo digimon, EvolutionInfo enemy, int vaccineTotal, int dataTotal, int virusTotal) {
        Enum.Attribute attack;
        boolean defend = false;
        Enum.Attribute attribute = attack = isPlayer ? this._attribute : this._enemy.getOppAttribute();
        if (isPlayer ? this._health > this._fullHealth / 2 : this._enemyHealth > this._enemy.getEnemyHealth() / 2) {
            int[] values = this.calcBruteStrategyValues(isPlayer, digimon, enemy, vaccineTotal, dataTotal, virusTotal);
            Enum.Attribute choice = this.checkAttackTotalAndZero(isPlayer, vaccineTotal = values[0], dataTotal = values[1], virusTotal = values[2]);
            if (choice == Enum.Attribute.None) {
                defend = true;
            } else {
                attack = choice;
            }
        } else {
            defend = true;
        }
        if (defend) {
            attack = this.defenseStrategy(isPlayer, digimon, enemy, vaccineTotal, dataTotal, virusTotal);
        }
        return attack;
    }

    private Enum.Attribute defenseStrategy(boolean isPlayer, EvolutionInfo digimon, EvolutionInfo enemy, int vaccineTotal, int dataTotal, int virusTotal) {
        Enum.Attribute choice;
        Enum.AttackCondition c;
        boolean valid = false;
        Iterator<Enum.AttackCondition> iterator = digimon.getVaccineConditions().iterator();
        while (iterator.hasNext() && (valid = this._process.checkCondition(c = iterator.next(), isPlayer))) {
        }
        if (valid) {
            vaccineTotal += this.checkDefendWeight(digimon.getVaccineEffect(), isPlayer);
        }
        valid = false;
        iterator = digimon.getDataConditions().iterator();
        while (iterator.hasNext() && (valid = this._process.checkCondition(c = iterator.next(), isPlayer))) {
        }
        if (valid) {
            dataTotal += this.checkDefendWeight(digimon.getDataEffect(), isPlayer);
        }
        valid = false;
        iterator = digimon.getVirusConditions().iterator();
        while (iterator.hasNext() && (valid = this._process.checkCondition(c = iterator.next(), isPlayer))) {
        }
        if (valid) {
            virusTotal += this.checkDefendWeight(digimon.getVirusEffect(), isPlayer);
        }
        Enum.Attribute attack = (choice = this.checkAttackTotalAndZero(isPlayer, vaccineTotal, dataTotal, virusTotal)) == Enum.Attribute.None ? this.checkZeroAttackSubstitute(isPlayer, vaccineTotal, dataTotal, virusTotal) : choice;
        return attack;
    }

    private Enum.Attribute checkAttackTotalAndZero(boolean isPlayer, int vaccineTotal, int dataTotal, int virusTotal) {
        Enum.Attribute attack = Enum.Attribute.None;
        if (vaccineTotal > dataTotal && vaccineTotal > virusTotal && (isPlayer ? this._zeroAttack != Enum.Attribute.Vaccine : this._zeroEnemyAttack != Enum.Attribute.Vaccine)) {
            attack = Enum.Attribute.Vaccine;
        } else if (dataTotal > vaccineTotal && dataTotal > virusTotal && (isPlayer ? this._zeroAttack != Enum.Attribute.Data : this._zeroEnemyAttack != Enum.Attribute.Data)) {
            attack = Enum.Attribute.Data;
        } else if (virusTotal > vaccineTotal && virusTotal > dataTotal && (isPlayer ? this._zeroAttack != Enum.Attribute.Virus : this._zeroEnemyAttack != Enum.Attribute.Virus)) {
            attack = Enum.Attribute.Virus;
        } else if ((isPlayer ? this._zeroAttack != Enum.Attribute.Virus : this._zeroEnemyAttack != Enum.Attribute.Virus) && virusTotal > 0 && (virusTotal == dataTotal || virusTotal == vaccineTotal)) {
            if (this._attackYellow > this._attackGreen || this._attackYellow > this._attackRed) {
                attack = Enum.Attribute.Virus;
            }
        } else if ((isPlayer ? this._zeroAttack != Enum.Attribute.Data : this._zeroEnemyAttack != Enum.Attribute.Data) && dataTotal > 0 && (dataTotal == virusTotal || dataTotal == vaccineTotal)) {
            if (this._attackYellow < this._attackGreen || this._attackGreen > this._attackRed) {
                attack = Enum.Attribute.Data;
            }
        } else if (!(!(isPlayer ? this._zeroAttack != Enum.Attribute.Vaccine : this._zeroEnemyAttack != Enum.Attribute.Vaccine) || vaccineTotal <= 0 || vaccineTotal != dataTotal && vaccineTotal != virusTotal || this._attackRed <= this._attackGreen && this._attackYellow >= this._attackRed)) {
            attack = Enum.Attribute.Vaccine;
        }
        return attack;
    }

    private Enum.Attribute bruteStrategy(boolean isPlayer, EvolutionInfo digimon, EvolutionInfo enemy, int vaccineTotal, int dataTotal, int virusTotal) {
        int[] values = this.calcBruteStrategyValues(isPlayer, digimon, enemy, vaccineTotal, dataTotal, virusTotal);
        Enum.Attribute choice = this.checkAttackTotalAndZero(isPlayer, vaccineTotal = values[0], dataTotal = values[1], virusTotal = values[2]);
        Enum.Attribute attack = choice == Enum.Attribute.None ? this.checkZeroAttackSubstitute(isPlayer, vaccineTotal, dataTotal, virusTotal) : choice;
        return attack;
    }

    private int[] calcBruteStrategyValues(boolean isPlayer, EvolutionInfo digimon, EvolutionInfo enemy, int vaccineTotal, int dataTotal, int virusTotal) {
        Enum.AttackCondition c;
        boolean valid = false;
        Iterator<Enum.AttackCondition> iterator = digimon.getVaccineConditions().iterator();
        while (iterator.hasNext() && (valid = this._process.checkCondition(c = iterator.next(), isPlayer))) {
        }
        if (valid) {
            vaccineTotal += this.checkAttackWeight(digimon.getVaccineEffect());
        }
        iterator = enemy.getVaccineConditions().iterator();
        while (iterator.hasNext() && (valid = this._process.checkCondition(c = iterator.next(), !isPlayer))) {
        }
        if (valid) {
            this.checkForceAttribute(enemy.getVaccineEffect(), isPlayer);
        }
        valid = false;
        iterator = digimon.getDataConditions().iterator();
        while (iterator.hasNext() && (valid = this._process.checkCondition(c = iterator.next(), isPlayer))) {
        }
        if (valid) {
            dataTotal += this.checkAttackWeight(digimon.getDataEffect());
        }
        iterator = enemy.getDataConditions().iterator();
        while (iterator.hasNext() && (valid = this._process.checkCondition(c = iterator.next(), !isPlayer))) {
        }
        if (valid) {
            this.checkForceAttribute(enemy.getDataEffect(), isPlayer);
        }
        valid = false;
        iterator = digimon.getVirusConditions().iterator();
        while (iterator.hasNext() && (valid = this._process.checkCondition(c = iterator.next(), isPlayer))) {
        }
        if (valid) {
            virusTotal += this.checkAttackWeight(digimon.getVirusEffect());
        }
        iterator = enemy.getVirusConditions().iterator();
        while (iterator.hasNext() && (valid = this._process.checkCondition(c = iterator.next(), !isPlayer))) {
        }
        if (valid) {
            this.checkForceAttribute(enemy.getVirusEffect(), isPlayer);
        }
        return new int[]{vaccineTotal, dataTotal, virusTotal};
    }

    private Enum.Attribute checkZeroAttackSubstitute(boolean isPlayer, int vaccineTotal, int dataTotal, int virusTotal) {
        Enum.Attribute attack = isPlayer ? this._attribute : this._enemy.getOppAttribute();
        switch (isPlayer ? this._zeroAttack : this._zeroEnemyAttack) {
            case Vaccine: {
                if (dataTotal > virusTotal) {
                    attack = Enum.Attribute.Data;
                    break;
                }
                attack = Enum.Attribute.Virus;
                break;
            }
            case Data: {
                if (vaccineTotal > virusTotal) {
                    attack = Enum.Attribute.Vaccine;
                    break;
                }
                attack = Enum.Attribute.Virus;
                break;
            }
            case Virus: {
                attack = vaccineTotal > dataTotal ? Enum.Attribute.Vaccine : Enum.Attribute.Data;
            }
        }
        return attack;
    }

    private int checkAttackWeight(Enum.AttackEffect effect) {
        int total = 0;
        switch (effect) {
            case AttackUp: 
            case Leech: {
                total = 1;
            }
        }
        return total;
    }

    private int checkDefendWeight(Enum.AttackEffect effect, boolean isPlayer) {
        int total = 0;
        switch (effect) {
            case AttackUp: 
            case Leech: 
            case Counter: {
                total = -1;
                break;
            }
            case Weaken: 
            case Heal: {
                double health;
                double d = health = isPlayer ? (double)this._health : (double)this._enemyHealth;
                double healthC = health > 0.0 ? 1.0 - health / (double)(isPlayer ? this._enemyHealth : this._health) : 1.0;
                int n = isPlayer ? this._enemyHealth : this._health;
                if (health < (double)n) {
                    total = (int)Math.round(Math.pow(5.0, healthC));
                    break;
                }
                total = -2;
                break;
            }
            case DefenseUp: 
            case Absorb: {
                total = 2;
                break;
            }
            case DisableAttack: {
                total = 5;
                break;
            }
            case ForceOppVaccine: 
            case ForceOppData: 
            case ForceOppVirus: {
                total = 1;
                break;
            }
            case DisableEffect: 
            case First: {
                total = 3;
            }
        }
        return total;
    }

    private void checkForceAttribute(Enum.AttackEffect effect, boolean isPlayer) {
        Random r = new Random();
        int i = r.nextInt(5);
        if (i == 3) {
            switch (effect) {
                case ForceOppVaccine: {
                    if ((isPlayer ? this._attackType : this._oppAttack) == Enum.Attribute.Vaccine) break;
                    if (isPlayer) {
                        this._zeroAttack = Enum.Attribute.Vaccine;
                        break;
                    }
                    this._zeroEnemyAttack = Enum.Attribute.Vaccine;
                    break;
                }
                case ForceOppData: {
                    if ((isPlayer ? this._attackType : this._oppAttack) == Enum.Attribute.Data) break;
                    if (isPlayer) {
                        this._zeroAttack = Enum.Attribute.Data;
                        break;
                    }
                    this._zeroEnemyAttack = Enum.Attribute.Data;
                    break;
                }
                case ForceOppVirus: {
                    if ((isPlayer ? this._attackType : this._oppAttack) == Enum.Attribute.Virus) break;
                    if (isPlayer) {
                        this._zeroAttack = Enum.Attribute.Virus;
                        break;
                    }
                    this._zeroEnemyAttack = Enum.Attribute.Virus;
                }
            }
        }
    }

    private Enum.Attribute randomAI(boolean isPlayer) {
        Enum.Attribute attack = Enum.Attribute.None;
        int red = isPlayer ? this._attackRed : this._enemy.getOppRed();
        int green = isPlayer ? this._attackGreen : this._enemy.getOppGreen();
        int yellow = isPlayer ? this._attackYellow : this._enemy.getOppYellow();
        ArrayList<Enum.Attribute> valid = new ArrayList<Enum.Attribute>();
        if (red > 0) {
            valid.add(Enum.Attribute.Vaccine);
        }
        if (green > 0) {
            valid.add(Enum.Attribute.Data);
        }
        if (yellow > 0) {
            valid.add(Enum.Attribute.Virus);
        }
        if (valid.size() > 0) {
            Random r = new Random();
            int i = r.nextInt(valid.size());
            attack = (Enum.Attribute)((Object)valid.get(i));
        }
        return attack;
    }

    private Enum.Attribute bruteAI(Enum.Attribute attribute, int red, int green, int yellow, boolean isPlayer) {
        Enum.Attribute attack = attribute;
        if (attribute == Enum.Attribute.None) {
            attack = red > yellow && red > green ? Enum.Attribute.Vaccine : (green > red && green > yellow ? Enum.Attribute.Data : (yellow > red && yellow > green ? Enum.Attribute.Virus : Enum.Attribute.Data));
        }
        int attackPower = this.calcAttackPower(attack, isPlayer);
        int vaccinePower = this.calcAttackPower(Enum.Attribute.Vaccine, isPlayer);
        int dataPower = this.calcAttackPower(Enum.Attribute.Data, isPlayer);
        int virusPower = this.calcAttackPower(Enum.Attribute.Virus, isPlayer);
        if (vaccinePower > attackPower && vaccinePower > dataPower && vaccinePower > virusPower && (isPlayer ? this._zeroAttack != Enum.Attribute.Vaccine : this._zeroEnemyAttack != Enum.Attribute.Vaccine)) {
            attack = Enum.Attribute.Vaccine;
        } else if (dataPower > attackPower && dataPower > vaccinePower && dataPower > virusPower && (isPlayer ? this._zeroAttack != Enum.Attribute.Data : this._zeroEnemyAttack != Enum.Attribute.Data)) {
            attack = Enum.Attribute.Data;
        } else if (virusPower > attackPower && virusPower > vaccinePower && virusPower > dataPower && (isPlayer ? this._zeroAttack != Enum.Attribute.Virus : this._zeroEnemyAttack != Enum.Attribute.Virus)) {
            attack = Enum.Attribute.Virus;
        } else {
            switch (isPlayer ? this._zeroAttack : this._zeroEnemyAttack) {
                case Vaccine: {
                    if (dataPower > virusPower) {
                        attack = Enum.Attribute.Data;
                        break;
                    }
                    attack = Enum.Attribute.Virus;
                    break;
                }
                case Data: {
                    if (vaccinePower > virusPower) {
                        attack = Enum.Attribute.Vaccine;
                        break;
                    }
                    attack = Enum.Attribute.Virus;
                    break;
                }
                case Virus: {
                    attack = vaccinePower > dataPower ? Enum.Attribute.Vaccine : Enum.Attribute.Data;
                }
            }
        }
        return attack;
    }

    public void checkFinish() {
        if (this._health <= 0 || this._enemyHealth <= 0) {
            this._inProgress = false;
        }
    }

    public boolean battleEnd() {
        byte bonus;
        boolean complied = this._digimon.checkCompliant();
        byte by = bonus = this._digimon.getIsFree() ? Config._noOrdersBattleStatIncBonus : (byte)0;
        if (this._digimon.getExercise() < Config._battleMaxStrengthInc) {
            this._digimon.setExercise((byte)(this._digimon.getExercise() + Config._battleExerciseInc), this._enemy.getOppAttribute(), Config._rankChangeFatigue, complied);
        }
        this._digimon.incExerciseTime();
        boolean won = false;
        if (this._health <= 0) {
            this._digimon.setCurrentState(Enum.State.Losing);
            this._digimon.setObedience(this._digimon.getObedience() - Config._battlesObedienceDec);
            this._digimon.setMistakeDay(this._digimon.getMistakeDay() + Config._battleLostMistakeDayChange);
            this._digimon.setMood(this._digimon.getMood() - Config._battleLostMoodDec + Config._battleDispositionMoodFactor * this._digimon.getDisposition());
            this._digimon.setEnergy((byte)(this._digimon.getEnergy() - Config._battleLostEnergyDec));
            this._digimon.setEnthusiasm((byte)(this._digimon.getEnthusiasm() - Config._battleLostEnthusiasmDec));
            if (this._digimon.checkWorseSick(Config._battleLostWorseSickChance) && complied) {
                this._digimon.setObedience(this._digimon.getObedience() + Config._obedienceChangeSickForced);
            }
            if (this._digimon.getSurrender() == 2) {
                this._digimon.setObedience(Config._surrenderRequestDeclinedLostBattleObedienceDec);
            }
            if (this._battleType == BattleType.PvE_Tourney) {
                this._digimon.getTournament().getChecked().add(this._digimon.getTournament().getCurrentEnemy());
                if (!this._digimon.getTournament().getNPCWon()) {
                    this._digimon.setCurrentState(Enum.State.NPC_Fight);
                } else {
                    this._digimon.getTournament().clearChecked();
                    this._digimon.setCurrentState(Enum.State.Tourney_Trophy);
                }
                this._digimon.getTournament().setIsWon(0);
            }
            this._digimon.changeMoodRank(Config._rankChangeBattleLost);
            this._digimon.changeBattleRanks(this._enemy.getOppAttribute(), Config._rankChangeBattleLost + (complied ? Config._rankChangeBattleForced : (byte)0));
            this._digimon.checkBattleInj(this._enemy.getOppAttribute(), false, complied);
        } else if (this._enemyHealth <= 0) {
            won = true;
            this._digimon.incAttRank(this._enemy.getOppAttribute());
            this._digimon.setCurrentState(Enum.State.Winning);
            switch (this._digimon.compareStage(this._enemy.getOppStage())) {
                case -1: {
                    if (this._enemy.getEnemyHealth() > this.getOppMaxHealth() || this._enemy.getEnemyHealth() >= this._fullHealth) break;
                    this._digimon.setMood(this._digimon.getMood() - Config._overpoweredBattleWonMoodDec + Config._battleDispositionMoodFactor * this._digimon.getDisposition());
                    break;
                }
                case 1: {
                    if (this._enemy.getEnemyHealth() < this.getOppMaxHealth() || this._enemy.getEnemyHealth() <= this._fullHealth) break;
                    this._digimon.setMood(this._digimon.getMood() + Config._underpoweredBattleWonMoodInc + Config._battleDispositionMoodFactor * this._digimon.getDisposition());
                }
            }
            this._digimon.setMood(this._digimon.getMood() + Config._battleWonMoodInc + Config._battleDispositionMoodFactor * this._digimon.getDisposition());
            this._digimon.setEnthusiasm((byte)(this._digimon.getEnthusiasm() - Config._battleWonEnthusiasmDec));
            this._digimon.setEnergy((byte)(this._digimon.getEnergy() - Config._battleWonEnergyDec));
            this._digimon.setPraise(true);
            if (this._digimon.checkWorseSick(Config._battleWonWorseSickChance) && complied) {
                this._digimon.setObedience(this._digimon.getObedience() + Config._obedienceChangeSickForced);
            }
            this._digimon.checkBattleInj(this._enemy.getOppAttribute(), true, complied);
            WorldMap world = this._digimon.getWorld();
            this.incLevelFought();
            this._digimon.setWins(this._digimon.getWins() + 1);
            this.incStats(bonus);
            this._digimon.checkAndIncPerfectWins(false);
            if (this._battleType == BattleType.PvE_Wild) {
                if (world.getCurrentZone().getTotalSteps() <= world.getCurrentZone().getCurrentLocation()) {
                    this._digimon.getWorld().setTravelSpeed((byte)0);
                    this._digimon.setCurrentState(Enum.State.ZoneChange);
                }
                if (this._item != null || this._bitsWon != 0) {
                    if (this._item != null) {
                        if (this._item.isFood()) {
                            for (FoodType f : this._digimon.getFoodTypes()) {
                                if (f.getID() != this._item.getConsumableID()) continue;
                                f.unlockFood(this._digimon);
                                break;
                            }
                        } else {
                            for (Item item : this._digimon.getItems()) {
                                if (item.getID() != this._item.getConsumableID()) continue;
                                item.unlockItem(this._digimon);
                                break;
                            }
                        }
                    }
                    if (this._bitsWon != 0) {
                        this._digimon.setCurrentState(Enum.State.EarningBits);
                    }
                }
            } else if (this._battleType == BattleType.PvE_Tourney) {
                this._digimon.getTournament().getDisqualified().add(this._digimon.getTournament().getCurrentEnemy());
                this._digimon.getTournament().checkWon();
                if (this._digimon.getTournament().getIsWon() == 2) {
                    this._digimon.setCurrentState(Enum.State.Tourney_Trophy);
                } else {
                    this._digimon.setCurrentState(Enum.State.NPC_Fight);
                }
            }
        }
        if ((double)this._health > Math.ceil(this._fullHealth / Config._battleLowHealthCoefficient)) {
            this._digimon.setEnergy((byte)(this._digimon.getEnergy() - Config._battleHighHealthEnergyDec));
            this._digimon.setCaloriesAndChangeWeight(this._digimon.getCalories() - Config._battleCalorieDecHighHealth);
        } else {
            this._digimon.setEnergy((byte)(this._digimon.getEnergy() - Config._battleLowHealthEnergyDec));
            this._digimon.setCaloriesAndChangeWeight(this._digimon.getCalories() - Config._battleCalorieDecLowHealth);
        }
        this.checkSick();
        this._digimon.setBattles(this._digimon.getBattles() + 1);
        this._digimon.setHealthPoints(this._health);
        if (complied) {
            this._digimon.changeMoodRank(Config._rankChangeMoodBattleForced);
        }
        this._digimon.setWeight(this._digimon.getWeight() - Config._battleWeightDec);
        if (this._battleType == BattleType.PvE_Wild) {
            this._digimon.setBattleImmunity(true);
        }
        if (this._digimon.getDislikedTime() == this._digimon.checkTime(this._digimon.getClock().getHours())) {
            this._digimon.setEnthusiasm((byte)(this._digimon.getEnthusiasm() + Config._dislikedTimeBattleEnthusiasmChange));
            this._digimon.setMood(this._digimon.getMood() + Config._dislikedTimeBattleMoodChange);
        }
        if (this._digimon.getDisposition() > 0 && complied) {
            this._digimon.setEnthusiasm((byte)(this._digimon.getEnthusiasm() + Config._enthusiasmChangeDislikeForced));
        }
        if (!this._digimon.getIsFree()) {
            this._digimon.setObedience(this._digimon.getObedience() + Config._battleFreeObedienceInc);
            if (won) {
                this._digimon.setMood(this._digimon.getMood() + Config._ordersWonMoodInc + Config._battleDispositionMoodFactor * -this._digimon.getDisposition());
            }
        }
        this._digimon.autoSave();
        this._battleType = BattleType.None;
        return won;
    }

    public int getBaseAttack(Enum.Stage s) {
        switch (s) {
            case Fresh: {
                return Config._freshBaseAttack;
            }
            case InTraining: {
                return Config._inTrainingBaseAttack;
            }
            case Rookie: {
                return Config._rookieBaseAttack;
            }
            case Champion: {
                return Config._championBaseAttack;
            }
            case Ultimate: {
                return Config._ultimateBaseAttack;
            }
            case Mega: {
                return Config._megaBaseAttack;
            }
        }
        return Config._rookieBaseAttack;
    }

    private int getOppMaxHealth() {
        switch (this._enemy.getOppStage()) {
            case Rookie: {
                return Config._maxHealthRookie;
            }
            case Champion: {
                return Config._maxHealthChampion;
            }
            case Ultimate: {
                return Config._maxHealthUltimate;
            }
            case Mega: {
                return Config._maxHealthUltra;
            }
        }
        return Config._maxHealthDefault;
    }

    private void incLevelFought() {
        this._digimon.addLevelFought(this.getEnemyLevel());
    }

    public int getEnemyLevel() {
        int diff = 1;
        switch (this._oppDifficulty) {
            case 0: {
                diff = 2;
                break;
            }
            case 1: {
                diff = 1;
                break;
            }
            case 2: {
                diff = 3;
            }
        }
        return this._digimon.getLevel(this._enemy.getOppRed() / diff, this._enemy.getOppGreen() / diff, this._enemy.getOppYellow() / diff, this._enemy.getEnemyHealth());
    }

    private void incStats(int bonus) {
        int inc = bonus;
        Enum.Attribute a = this._enemy.getOppAttribute();
        int max = 0;
        int[] att = new int[]{this._enemy.getOppRed(), this._enemy.getOppGreen(), this._enemy.getOppYellow()};
        for (int i = 0; i < att.length; ++i) {
            if (att[i] <= max && (att[i] != max || !Utility.randomChance(0, 2))) continue;
            max = att[i];
            a = Enum.Attribute.values()[i];
        }
        this.incStatsByAttribute(a, inc);
    }

    private void incStatsByAttribute(Enum.Attribute a, int inc) {
        switch (a) {
            case Vaccine: {
                this._digimon.setVaccinePower(this._digimon.getVaccinePower() + (inc += this.getExtraStats(this._enemy.getOppRed())));
                break;
            }
            case Data: {
                this._digimon.setDataPower(this._digimon.getDataPower() + (inc += this.getExtraStats(this._enemy.getOppGreen())));
                break;
            }
            case Virus: {
                this._digimon.setVirusPower(this._digimon.getVirusPower() + (inc += this.getExtraStats(this._enemy.getOppYellow())));
            }
        }
    }

    private int getExtraStats(int oppPower) {
        int inc = (int)Math.ceil((double)oppPower / (double)Config._battleMinOppAttributeBonus);
        return inc <= Config._battleMaxAttributeBonus ? inc : (int)Config._battleMaxAttributeBonus;
    }

    public boolean chooseAttack(Enum.Attribute att, boolean isFreeWill, boolean skipPlayer) {
        boolean obey = true;
        if (!skipPlayer) {
            if (!isFreeWill && !this._digimon.refuseAttack(this)) {
                this.setAttackType(att);
            } else {
                this.playerAttackChoose();
                boolean bl = skipPlayer = this._attackType == Enum.Attribute.None;
                if (!(skipPlayer || isFreeWill || this._digimon.getIsFree())) {
                    obey = false;
                    this._digimon.setScoldWindow((byte)0);
                    this._digimon.setScold(true);
                }
            }
        } else {
            this.setAttackType(Enum.Attribute.None);
        }
        this.checkFirst(skipPlayer);
        return obey;
    }

    public void surrender() {
        this._inProgress = false;
        if (!this._enemy.getIsRandom()) {
            this._digimon.setBattles(this._digimon.getBattles() + 1);
        }
        this._digimon.setEnergy((byte)(this._digimon.getEnergy() - Config._surrenderEnergyDec));
        this._digimon.setWeight(this._digimon.getWeight() - Config._surrenderWeightDec);
        this._digimon.setEnthusiasm((byte)(this._digimon.getEnthusiasm() - Config._surrenderEnthusiasmDec));
        this.checkSick();
        this._battleType = BattleType.None;
    }

    public void escape() {
        this._inProgress = false;
        this._digimon.setCurrentState(Enum.State.Jeering);
        this._digimon.checkBattleInj(this._enemy.getOppAttribute(), false, false);
        this._digimon.checkWorseSick(Config._escapeWorseSickChance);
        this._digimon.setMood(this._digimon.getMood() - Config._escapeMoodDec);
        this._digimon.setEnergy((byte)(this._digimon.getEnergy() - Config._escapeEnergyDec));
        if (this._digimon.getEnergy() <= 0) {
            this._digimon.checkBattleInj(this._enemy.getOppAttribute(), false, false);
            this._digimon.checkWorseSick(Config._escapeWorseSickChance);
        }
        this._digimon.setEnthusiasm((byte)(this._digimon.getEnthusiasm() - Config._escapeEnthusiasmDec));
        this._digimon.setWeight(this._digimon.getWeight() - Config._escapeWeightDec);
        this.checkSick();
        this._battleType = BattleType.None;
    }

    private void checkSick() {
        if (this._enemyIsSick) {
            this._digimon.checkSick(Config._enemySickChance);
        }
    }

    private void setupOpponents(Enemy enemy) {
        int pvpBonus = 1;
        if (this._battleType == BattleType.PvP) {
            pvpBonus = Config._pvpBonusPowerMultiple;
        }
        int bonus = this._digimon.getIsFree() ? 1 : 0;
        this._attackRed = (this._digimon.getVaccinePower() + bonus) * pvpBonus;
        this._attackGreen = (this._digimon.getDataPower() + bonus) * pvpBonus;
        this._attackYellow = (this._digimon.getVirusPower() + bonus) * pvpBonus;
        this._health = this._digimon.getHealthPoints();
        this._fullHealth = this._digimon.getFullHealthPoints();
        this._attribute = this._digimon.getAttribute();
        this._field = this._digimon.getField();
        this._element = this._digimon.getElement();
        this._digimonIndex = this._digimon.getIndex();
        this._enemyHealth = enemy.getEnemyHealth();
        this._enemy = enemy;
        this._enemyIsSick = enemy.getIsSick();
        Random r = new Random();
        this._item = this.randomEnemyItem(r, enemy);
        int[] bits = enemy.getBitsWon();
        if (bits[1] != 0 || bits[0] != 0) {
            int range;
            this._bitsWon = bits[1] > bits[0] ? r.nextInt((range = bits[1] - bits[0] + 1) == 0 ? 1 : range) + bits[0] : bits[0];
        }
        this._enemy.setAI(enemy.getAI() != null ? enemy.getAI() : this.randomizeAI(this._enemy.getIsZoneBoss()));
    }

    private ConsumableDrops randomEnemyItem(Random r, Enemy enemy) {
        ConsumableDrops item = null;
        if (enemy.getItems() != null) {
            ConsumableDrops[] items = enemy.getAvailableConsumables(this._digimon);
            int[][] itemRange = new int[items.length][2];
            for (int i = 0; i < items.length; ++i) {
                itemRange[i][0] = i - 1 >= 0 ? itemRange[i - 1][1] + 1 : 1;
                itemRange[i][1] = itemRange[i][0] + items[i].getRate() - 1;
            }
            int randomResult = r.nextInt(100) + 1;
            for (int i = 0; i < itemRange.length; ++i) {
                if (itemRange[i][0] > randomResult || itemRange[i][1] < randomResult) continue;
                item = items[i];
                break;
            }
        }
        return item;
    }

    private Enum.AIType randomizeAI(boolean isBoss) {
        Enum.AIType ai = Enum.AIType.Random;
        int i = 0;
        Random r = new Random();
        if (isBoss) {
            i = r.nextInt(3) + 2;
        } else {
            i = r.nextInt(3);
            if (i == 2) {
                i = r.nextInt(3) + 2;
            }
        }
        ai = Enum.AIType.values()[i];
        return ai;
    }

    public void processHealthChange(boolean isEnemy) {
        String s = "";
        if (isEnemy) {
            s = "HP " + this.getEnemyHealth() + " -> ";
            this.setEnemyHealth(this.getEnemyHealth() + this._process.getEnemyHealthChange());
            s = s + this.getEnemyHealth();
        } else {
            s = "HP " + this.getHealth() + " -> ";
            this.setHealth(this.getHealth() + this._process.getPlayerHealthChange());
            s = s + this.getHealth();
        }
        this._battleRecord.add(s);
        this._battleRecord.add("");
    }

    public void checkAbsorbsDamage(boolean isEnemy) {
        if (isEnemy ? this._process.getEnemyEffect() == Enum.AttackEffect.Absorb : this._process.getPlayerEffect() == Enum.AttackEffect.Absorb) {
            String name = this._digimon.getEvolution().getDigimon(this._digimonIndex).getName();
            String enemyName = this._digimon.getEvolution().getDigimon(this._enemy.getIndex()).getName();
            this._battleRecord.add((isEnemy ? enemyName + " (O)" : name + " (P)") + " absorbs the attack:");
            this.processHealthChange(isEnemy);
        }
    }

    public void checkLeechOrSacrificeHealth(boolean isEnemy) {
        boolean sacrifice;
        Enum.AttackEffect effect = isEnemy ? this._process.getEnemyEffect() : this._process.getPlayerEffect();
        boolean bl = sacrifice = isEnemy ? this._process.getEnemyConditions().contains((Object)Enum.AttackCondition.SacrificeHealth) : this._process.getPlayerConditions().contains((Object)Enum.AttackCondition.SacrificeHealth);
        if (effect == Enum.AttackEffect.Leech || sacrifice) {
            String name = this._digimon.getEvolution().getDigimon(this._digimonIndex).getName();
            String enemyName = this._digimon.getEvolution().getDigimon(this._enemy.getIndex()).getName();
            this._battleRecord.add((isEnemy ? enemyName + " (O)" : name + " (P)") + (effect == Enum.AttackEffect.Leech ? " leeches" : " sacrifices") + " health:");
            this.processHealthChange(isEnemy);
        }
    }

    public void checkHeal(boolean isEnemy) {
        Enum.AttackEffect effect;
        Enum.AttackEffect attackEffect = effect = isEnemy ? this._process.getEnemyEffect() : this._process.getPlayerEffect();
        if (effect == Enum.AttackEffect.Heal) {
            String name = this._digimon.getEvolution().getDigimon(this._digimonIndex).getName();
            String enemyName = this._digimon.getEvolution().getDigimon(this._enemy.getIndex()).getName();
            this._battleRecord.add((isEnemy ? enemyName + " (O)" : name + " (P)") + " heals");
            this.processHealthChange(isEnemy);
        }
    }

    public void resetTurn() {
        this._battleRecord.add("*************");
        this._battleRecord.add("");
        this._digimon.setSurrender((byte)0);
        this.setAttack(0);
        this.setEnemyAttack(0);
        this._process.setProcessed(false);
        this._process.setEnemyHealthChange(0);
        this._process.setPlayerHealthChange(0);
    }

    public void addToBattleRecord(String[] record) {
        if (this._battleRecord != null) {
            this._battleRecord.addAll(Arrays.asList(record));
        }
    }

    public static enum BattleType {
        None,
        PvP,
        PvE_Wild,
        PvE_Tourney;

    }
}

