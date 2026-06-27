/*
 * Decompiled with CFR 0.152.
 */
package Model;

import Controller.Utility;
import Model.Battle;
import Model.Config;
import Model.Enemy;
import Model.Enum;
import Model.EvolutionInfo;
import Model.PhysicalState;
import Model.Trophy;
import java.awt.Point;
import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.util.ArrayList;
import java.util.Random;

public class Tournament {
    private final String MOD_FOLDER;
    private final String MODEL_FOLDER;
    private PhysicalState _digimon;
    private boolean _active;
    private Trophy _currentTrophy;
    private int _bits;
    private ArrayList<Trophy> _trophies;
    private ArrayList<Trophy> _springTrophies;
    private ArrayList<Trophy> _summerTrophies;
    private ArrayList<Trophy> _fallTrophies;
    private ArrayList<Trophy> _winterTrophies;
    private ArrayList<Enemy> _checked = new ArrayList();
    private Enemy _leftEnemy;
    private Enemy _rightEnemy;
    private Point[] _rosterPairs;
    private Enemy[] _roster;
    private ArrayList<Enemy> _disqualified;
    private byte _isWon = 1;

    public int getBits() {
        return this._bits;
    }

    public void setBits(int b) {
        this._bits = b;
    }

    public boolean isCheckedFull() {
        boolean isFull = false;
        for (Enemy e : this._roster) {
            if (e != null && !this._disqualified.contains(e) && !(isFull = this._checked.contains(e))) break;
        }
        return isFull;
    }

    public void fillChecked() {
        for (Enemy e : this._roster) {
            this._checked.add(e);
        }
    }

    public void clearChecked() {
        this._checked.clear();
    }

    public ArrayList<Enemy> getChecked() {
        return this._checked;
    }

    public void resetEnemies() {
        this._leftEnemy = null;
        this._rightEnemy = null;
    }

    public Enemy getLeftEnemy() {
        return this._leftEnemy;
    }

    public void setLeftEnemy(Enemy e) {
        this._leftEnemy = e;
    }

    public Enemy getRightEnemy() {
        return this._rightEnemy;
    }

    public void setRightEnemy(Enemy e) {
        this._rightEnemy = e;
    }

    public boolean getActive() {
        return this._active;
    }

    public void setActive(boolean a) {
        this._active = a;
        if (this._active) {
            this.startNewTourney();
        } else {
            this.endTourney();
        }
    }

    public Trophy getCurrentTrophy() {
        return this._currentTrophy;
    }

    public void setCurrentTrophy(Trophy t) {
        this._currentTrophy = t;
    }

    public Trophy getTrophy(int id) {
        Trophy trophy = null;
        for (Trophy t : this._trophies) {
            if (t.getID() != id) continue;
            trophy = t;
            break;
        }
        return trophy;
    }

    public Trophy getTrophy(int spriteNum, int spriteSet, Enum.Season season) {
        Trophy trophy = null;
        block0 : switch (season) {
            case Spring: {
                for (Trophy t : this._springTrophies) {
                    if (t.getSpriteNum() != spriteNum || t.getSpriteSet() != spriteSet || t.getSeason() != season) continue;
                    trophy = t;
                    break block0;
                }
                break;
            }
            case Summer: {
                for (Trophy t : this._summerTrophies) {
                    if (t.getSpriteNum() != spriteNum || t.getSpriteSet() != spriteSet || t.getSeason() != season) continue;
                    trophy = t;
                    break block0;
                }
                break;
            }
            case Fall: {
                for (Trophy t : this._fallTrophies) {
                    if (t.getSpriteNum() != spriteNum || t.getSpriteSet() != spriteSet || t.getSeason() != season) continue;
                    trophy = t;
                    break block0;
                }
                break;
            }
            case Winter: {
                for (Trophy t : this._winterTrophies) {
                    if (t.getSpriteNum() != spriteNum || t.getSpriteSet() != spriteSet || t.getSeason() != season) continue;
                    trophy = t;
                    break block0;
                }
                break;
            }
        }
        return trophy;
    }

    public ArrayList<Trophy> getTrophies() {
        return this._trophies;
    }

    public ArrayList<Trophy> getSpringTrophies() {
        return this._springTrophies;
    }

    public ArrayList<Trophy> getSummerTrophies() {
        return this._summerTrophies;
    }

    public ArrayList<Trophy> getFallTrophies() {
        return this._fallTrophies;
    }

    public ArrayList<Trophy> getWinterTrophies() {
        return this._winterTrophies;
    }

    public boolean checkTourneyClosed(int start, int currentHour) {
        boolean closed = false;
        if (start > -1 && start != currentHour) {
            closed = true;
        }
        return closed;
    }

    public int getTrophyNum() {
        return this._winterTrophies.size() + this._fallTrophies.size() + this._summerTrophies.size() + this._springTrophies.size();
    }

    public Point[] getRosterPairs() {
        return this._rosterPairs;
    }

    public Enemy[] getRoster() {
        return this._roster;
    }

    public void setRoster(Enemy[] e) {
        this._roster = e;
    }

    public ArrayList<Enemy> getDisqualified() {
        return this._disqualified;
    }

    public byte getIsWon() {
        return this._isWon;
    }

    public void setIsWon(int w) {
        if (w == 0) {
            switch (this.checkRound()) {
                case 1: {
                    this._bits = 0;
                    break;
                }
                case 2: {
                    this._bits = this.calcBits() / 3;
                    break;
                }
                case 3: {
                    this._bits = this.calcBits() / 2;
                }
            }
        } else if (w == 2) {
            this._bits = this.calcBits();
        }
        this._isWon = (byte)w;
    }

    public Tournament(PhysicalState digimon, String mod, String model) {
        this.MOD_FOLDER = mod;
        this.MODEL_FOLDER = model;
        this._digimon = digimon;
        this.buildTrophies();
    }

    private void endTourney() {
        this._rosterPairs = null;
        this._checked = null;
        this.resetEnemies();
        this._disqualified = null;
        this._roster = null;
        if (this._isWon == 2) {
            this._currentTrophy.setSeasonBeat(true);
            this._currentTrophy.setEarned(true);
        }
        if (!this._currentTrophy.getSameDayRetry()) {
            this._digimon.getFoughtTrophiesToday().add(this._currentTrophy.getID());
        }
    }

    private void startNewTourney() {
        this._isWon = 1;
        this._bits = 0;
        this._rosterPairs = new Point[4];
        this._rosterPairs[0] = new Point(0, 1);
        this._rosterPairs[1] = new Point(2, 3);
        this._rosterPairs[2] = new Point(4, 5);
        this._rosterPairs[3] = new Point(6, 7);
        this._checked = new ArrayList();
        this._disqualified = new ArrayList();
        this._roster = this.randomEnemies();
        this.randomizeRoster();
    }

    private Enemy[] randomEnemies() {
        Enemy[] enemies = new Enemy[8];
        ArrayList<EvolutionInfo> digimon = this._digimon.getEvolution().getEvolDigimon();
        ArrayList<EvolutionInfo> valid = new ArrayList<EvolutionInfo>();
        Random r = new Random();
        Enum.Stage stage = this._currentTrophy.getStageByAge(this._digimon);
        for (EvolutionInfo d : digimon) {
            boolean isEligible = true;
            if (!d.getTournamentAble() || d.getNewStage() == Enum.Stage.Fresh || d.getNewStage() == Enum.Stage.InTraining || d.getNewStage() == Enum.Stage.Egg) {
                isEligible = false;
            }
            if (this._currentTrophy.getEnemyStage() != Enum.Stage.None && this._currentTrophy.getEnemyStage() != d.getNewStage()) {
                isEligible = false;
            } else if (this._currentTrophy.getEnemyStage() == Enum.Stage.None && (this._currentTrophy.getAgeLimit() != Enum.Stage.None && this._currentTrophy.getAgeLimit() != d.getNewStage() || this._currentTrophy.getAgeLimit() == Enum.Stage.None && (stage == Enum.Stage.None ? d.getNewStage() != Enum.Stage.Mega : d.getNewStage() != stage))) {
                isEligible = false;
            }
            if (isEligible && this._currentTrophy.getEnemyField() != Enum.Field.NA && this._currentTrophy.getEnemyField() != d.getNewField()) {
                isEligible = false;
            } else if (isEligible && this._currentTrophy.getEnemyField() == Enum.Field.NA && this._currentTrophy.getFieldRestriction() != Enum.Field.NA && this._currentTrophy.getFieldRestriction() != d.getNewField()) {
                isEligible = false;
            }
            if (isEligible && this._currentTrophy.getEnemyAttribute() != Enum.Attribute.NA && this._currentTrophy.getEnemyAttribute() != d.getNewAttribute()) {
                isEligible = false;
            } else if (isEligible && this._currentTrophy.getEnemyAttribute() == Enum.Attribute.NA && this._currentTrophy.getAttributeRestriction() != Enum.Attribute.NA && this._currentTrophy.getAttributeRestriction() != d.getNewAttribute()) {
                isEligible = false;
            }
            if (isEligible && this._currentTrophy.getEnemyElement() != Enum.Element.NA && this._currentTrophy.getEnemyElement() != d.getNewElement()) {
                isEligible = false;
            }
            if (!isEligible) continue;
            valid.add(d);
        }
        for (int i = 0; i < enemies.length; ++i) {
            EvolutionInfo d;
            d = (EvolutionInfo)valid.get(r.nextInt(valid.size()));
            Enemy e = new Enemy();
            e.setOppAttribute(d.getNewAttribute());
            e.setOppField(d.getNewField());
            e.setOppElement(d.getNewElement());
            e.setOppStage(d.getNewStage());
            e.setSpriteNum(d.getNewSpriteNum());
            e.setSpriteSet(d.getNewSpriteSet());
            e.setIndex(d.getIndex());
            e.setEnemyHealth(this.setHealth(e.getOppStage()));
            int maxPower = this._currentTrophy.getAgeLimit() == Enum.Stage.None && e.getOppStage() == Enum.Stage.Mega ? Config._tourneyRandomMaxPower : (e.getOppStage() == Enum.Stage.Rookie ? Config._tourneyRandomRookiePower : (e.getOppStage() == Enum.Stage.Champion ? Config._tourneyRandomChampPower : (e.getOppStage() == Enum.Stage.Ultimate ? Config._tourneyRandomUltPower : (e.getOppStage() == Enum.Stage.Mega ? Config._tourneyRandomMegaPower : 1))));
            int minPower = 0;
            switch (e.getOppStage()) {
                case Rookie: {
                    minPower = Config._tourneyRandomRookiePower / 3;
                    break;
                }
                case Champion: {
                    minPower = Config._tourneyRandomRookiePower;
                    break;
                }
                case Ultimate: {
                    minPower = Config._tourneyRandomChampPower;
                    break;
                }
                case Mega: {
                    minPower = this._currentTrophy.getAgeLimit() == Enum.Stage.None ? Config._tourneyRandomMinPower : Config._tourneyRandomUltPower;
                }
            }
            int totalPower = r.nextInt(maxPower - minPower + 1) + minPower;
            switch (e.getOppAttribute()) {
                case Virus: {
                    e.setOppYellow((int)((double)totalPower / Config._tourneyMainAttributeCoefficient));
                    e.setOppRed((int)((double)totalPower / Config._tourneyWeakAttributeCoefficient));
                    e.setOppGreen((int)((double)totalPower / Config._tourneyAttributeCoefficient));
                    break;
                }
                case Vaccine: {
                    e.setOppRed((int)((double)totalPower / Config._tourneyMainAttributeCoefficient));
                    e.setOppGreen((int)((double)totalPower / Config._tourneyWeakAttributeCoefficient));
                    e.setOppYellow((int)((double)totalPower / Config._tourneyAttributeCoefficient));
                    break;
                }
                case Data: {
                    e.setOppGreen((int)((double)totalPower / Config._tourneyMainAttributeCoefficient));
                    e.setOppYellow((int)((double)totalPower / Config._tourneyWeakAttributeCoefficient));
                    e.setOppRed((int)((double)totalPower / Config._tourneyAttributeCoefficient));
                    break;
                }
                case None: {
                    e.setOppGreen(totalPower / 3);
                    e.setOppYellow(totalPower / 3);
                    e.setOppRed(totalPower / 3);
                }
            }
            enemies[i] = e;
        }
        return enemies;
    }

    public int getEnemyIndex(Enemy e) {
        int index = -1;
        for (int i = 0; i < this._roster.length; ++i) {
            if (this._roster[i] != e) continue;
            index = i;
            break;
        }
        return index;
    }

    private int setHealth(Enum.Stage s) {
        int health = 0;
        Random r = new Random();
        switch (s) {
            case Rookie: {
                health = r.nextInt(Config._tourneyMinHealth) + (Config._maxHealthRookie - Config._tourneyMinHealth);
                break;
            }
            case Champion: {
                health = r.nextInt(Config._tourneyMinHealth) + (Config._maxHealthChampion - Config._tourneyMinHealth);
                break;
            }
            case Ultimate: {
                health = r.nextInt(Config._tourneyMinHealth) + (Config._maxHealthUltimate - Config._tourneyMinHealth);
                break;
            }
            case Mega: {
                health = this._currentTrophy.getAgeLimit() == Enum.Stage.None ? r.nextInt(Config._tourneyMinHealth * 2) + (Config._maxHealthUltra - Config._tourneyMinHealth * 2) : r.nextInt(Config._tourneyMinHealth) + (Config._maxHealthMega - Config._tourneyMinHealth);
            }
        }
        return health;
    }

    public int getTourneyTime(int id) {
        if (id > 23) {
            return -1;
        }
        return id;
    }

    public int[] randTrophyIDs(Enum.Season season, int[] trophies, int[] forcedTrophies) {
        ArrayList<Trophy> availableTrophies = new ArrayList<Trophy>();
        Random ran = new Random();
        switch (season) {
            case Spring: {
                availableTrophies.addAll(this._springTrophies);
                break;
            }
            case Summer: {
                availableTrophies.addAll(this._summerTrophies);
                break;
            }
            case Fall: {
                availableTrophies.addAll(this._fallTrophies);
                break;
            }
            case Winter: {
                availableTrophies.addAll(this._winterTrophies);
            }
        }
        ArrayList<Trophy> free = new ArrayList<Trophy>();
        ArrayList<Trophy> rookie = new ArrayList<Trophy>();
        ArrayList<Trophy> champ = new ArrayList<Trophy>();
        ArrayList<Trophy> ult = new ArrayList<Trophy>();
        ArrayList<Trophy> mega = new ArrayList<Trophy>();
        block12: for (Trophy t : availableTrophies) {
            boolean valid = true;
            if (forcedTrophies != null) {
                for (int i : forcedTrophies) {
                    if (t.getID() != i) continue;
                    valid = false;
                    break;
                }
            }
            if (!valid || !t.getRandomIncluded()) continue;
            switch (t.getAgeLimit()) {
                case Rookie: {
                    rookie.add(t);
                    continue block12;
                }
                case Champion: {
                    champ.add(t);
                    continue block12;
                }
                case Ultimate: {
                    ult.add(t);
                    continue block12;
                }
                case Mega: {
                    mega.add(t);
                    continue block12;
                }
            }
            free.add(t);
        }
        ArrayList<ArrayList<Trophy>> order = new ArrayList<ArrayList<Trophy>>();
        order.add(free);
        order.add(rookie);
        order.add(free);
        order.add(champ);
        order.add(free);
        order.add(ult);
        order.add(free);
        order.add(mega);
        int i = 0;
        block14: while (i < trophies.length) {
            for (ArrayList arrayList : order) {
                if (!arrayList.isEmpty()) {
                    Trophy add = (Trophy)arrayList.get(ran.nextInt(arrayList.size()));
                    if (i <= 23 && add.getTime() != Enum.Time.None && add.getTime() != this._digimon.checkTime(i)) continue;
                    arrayList.remove(add);
                    trophies[i] = add.getID();
                    if (++i < trophies.length) continue;
                    continue block14;
                }
                i = trophies.length;
                continue block14;
            }
        }
        if (forcedTrophies != null) {
            for (i = 0; i < forcedTrophies.length && trophies.length - 1 - i >= 0; ++i) {
                Trophy t = this.getTrophy(forcedTrophies[i]);
                if (t == null || t.getSeason() != season) continue;
                trophies[trophies.length - 1 - i] = forcedTrophies[i];
            }
        }
        return trophies;
    }

    public boolean isEligible() {
        boolean isEligible = true;
        if (this._digimon.getFoughtTrophiesToday().contains(this._currentTrophy.getID())) {
            isEligible = false;
        }
        if (isEligible && !this._digimon.isFullyRecovered()) {
            isEligible = false;
        }
        if (isEligible && this._currentTrophy.getAgeLimit() != Enum.Stage.None && this._currentTrophy.getAge() < this._digimon.getAge()) {
            isEligible = false;
        }
        if (isEligible && this._currentTrophy.getFieldRestriction() != Enum.Field.NA && this._currentTrophy.getFieldRestriction() != this._digimon.getField()) {
            isEligible = false;
        }
        if (isEligible && this._currentTrophy.getAttributeRestriction() != Enum.Attribute.NA && this._currentTrophy.getAttributeRestriction() != this._digimon.getAttribute()) {
            isEligible = false;
        }
        if (isEligible && this._currentTrophy.getPrelim() != 0 && !this.getTrophy(this._currentTrophy.getPrelim()).getSeasonBeat()) {
            isEligible = false;
        }
        return isEligible;
    }

    private void buildTrophies() {
        this._trophies = new ArrayList();
        this._springTrophies = new ArrayList();
        this._summerTrophies = new ArrayList();
        this._fallTrophies = new ArrayList();
        this._winterTrophies = new ArrayList();
        try (InputStream in = Utility.getInputStream(this.MOD_FOLDER, this.MODEL_FOLDER, "tournies.csv");
             BufferedReader reader = new BufferedReader(new InputStreamReader(in));){
            String line = reader.readLine();
            while ((line = reader.readLine()) != null) {
                Trophy trophy = new Trophy();
                this._trophies.add(trophy.readInfoString(line));
                switch (trophy.getSeason()) {
                    case Spring: {
                        this._springTrophies.add(trophy);
                        break;
                    }
                    case Summer: {
                        this._summerTrophies.add(trophy);
                        break;
                    }
                    case Fall: {
                        this._fallTrophies.add(trophy);
                        break;
                    }
                    case Winter: {
                        this._winterTrophies.add(trophy);
                    }
                }
            }
        }
        catch (Exception e) {
            e.printStackTrace();
        }
    }

    public void saveSchedule() {
    }

    public void checkNewSchedule() {
    }

    public void newSchedule() {
    }

    private void disqualify(Enemy opponent) {
        for (Enemy enemy : this._roster) {
            if (enemy == null || !enemy.equals(opponent)) continue;
            this._disqualified.add(enemy);
            break;
        }
    }

    private void randomizeRoster() {
        ArrayList<Enemy> enemies = new ArrayList<Enemy>();
        while (enemies.size() < this._roster.length - 1) {
            Random ran = new Random();
            Enemy toMove = this._roster[ran.nextInt(this._roster.length)];
            if (toMove == null || enemies.contains(toMove)) continue;
            enemies.add(toMove);
        }
        this._roster = enemies.toArray(new Enemy[enemies.size() + 1]);
        this.randomizePlayer();
    }

    public void checkWon() {
        if (this._disqualified.size() == this._roster.length - 1) {
            this.setIsWon(2);
        }
    }

    private void randomizePlayer() {
        Random ran = new Random();
        int index = ran.nextInt(this._roster.length);
        Enemy toMove = this._roster[index];
        for (int i = 0; i < this._roster.length; ++i) {
            if (this._roster[i] != null) continue;
            this._roster[i] = toMove;
            break;
        }
        this._roster[index] = null;
    }

    public Enemy getCurrentEnemy() {
        return this.checkMatchup(this.getPlayerIndex());
    }

    public void npcFight(int i) {
        this._leftEnemy = null;
        this._rightEnemy = null;
        Enemy leftEnemy = this._disqualified.contains(this._roster[i]) ? null : this._roster[i];
        Enemy rightEnemy = this.checkMatchup(i);
        if (!(this._checked.contains(leftEnemy) || this._checked.contains(rightEnemy) || leftEnemy == null || rightEnemy == null || this._disqualified.contains(rightEnemy))) {
            this._leftEnemy = leftEnemy;
            this._rightEnemy = rightEnemy;
            this.autoFight(this._leftEnemy, this._rightEnemy);
            this._checked.add(leftEnemy);
            this._checked.add(rightEnemy);
        }
    }

    public void autoFight(Enemy player, Enemy enemy) {
        int turns;
        Battle battle = new Battle(player, enemy, this._digimon);
        for (turns = 0; battle.getEnemyHealth() > 0 && battle.getHealth() > 0 && turns < 1000; ++turns) {
            battle.enemyAttackChoose();
            battle.playerAttackChoose();
            battle.checkFirst(false);
            battle.attack();
            if (battle.getPlayerFirst()) {
                battle.checkAbsorbsDamage(true);
                battle.finishAttack(battle.getEnemyHealth(), true);
                battle.checkLeechOrSacrificeHealth(false);
                battle.checkHeal(false);
                if (battle.getEnemyHealth() <= 0) break;
                battle.checkAbsorbsDamage(false);
                battle.finishAttack(battle.getHealth(), false);
                battle.checkLeechOrSacrificeHealth(true);
                battle.checkHeal(true);
                continue;
            }
            battle.checkAbsorbsDamage(false);
            battle.finishAttack(battle.getHealth(), false);
            battle.checkLeechOrSacrificeHealth(true);
            battle.checkHeal(true);
            if (battle.getHealth() <= 0) break;
            battle.checkAbsorbsDamage(true);
            battle.finishAttack(battle.getEnemyHealth(), true);
            battle.checkLeechOrSacrificeHealth(false);
            battle.checkHeal(false);
        }
        if (turns >= 1000) {
            int enemyStats;
            int playerStats = player.getOppRed() + player.getOppGreen() + player.getOppYellow() + battle.getHealth();
            if (playerStats > (enemyStats = enemy.getOppGreen() + enemy.getOppRed() + enemy.getOppYellow() + battle.getEnemyHealth())) {
                battle.setEnemyHealth(0);
            } else if (playerStats < enemyStats) {
                battle.setHealth(0);
            } else {
                Random r = new Random();
                int i = r.nextInt(2);
                if (i == 1) {
                    battle.setEnemyHealth(0);
                } else {
                    battle.setHealth(0);
                }
            }
        }
        if (battle.getHealth() <= 0) {
            this._disqualified.add(player);
        } else if (battle.getEnemyHealth() <= 0) {
            this._disqualified.add(enemy);
        }
    }

    public byte checkRound() {
        byte round = 0;
        round = this._isWon != 0 && this._disqualified.size() >= 4 && this._disqualified.size() < 6 || this._isWon == 0 && this._disqualified.size() >= 3 && this._disqualified.size() < 5 ? (byte)2 : (this._isWon != 0 && this._disqualified.size() >= 6 || this._isWon == 0 && this._disqualified.size() >= 5 ? (byte)3 : 1);
        return round;
    }

    private Enemy checkMatchup(int playerIndex) {
        Enemy currentEnemy = null;
        if (this._isWon != 0 && this._disqualified.size() >= 4 && this._disqualified.size() < 6 || this._isWon == 0 && this._disqualified.size() >= 3 && this._disqualified.size() < 5) {
            if (this.getPlayerBracket(playerIndex)) {
                int i = 0;
                while ((double)i < Math.floor(this._roster.length / 2)) {
                    if (i != playerIndex && this._roster[i] != null && !this._disqualified.contains(this._roster[i])) {
                        currentEnemy = this._roster[i];
                        break;
                    }
                    ++i;
                }
            } else {
                for (int i = (int)Math.floor(this._roster.length / 2); i < this._roster.length; ++i) {
                    if (i == playerIndex || this._roster[i] == null || this._disqualified.contains(this._roster[i])) continue;
                    currentEnemy = this._roster[i];
                    break;
                }
            }
        } else if (this._isWon != 0 && this._disqualified.size() >= 6 || this._isWon == 0 && this._disqualified.size() >= 5) {
            for (int i = 0; i < this._roster.length; ++i) {
                if (i == playerIndex || this._roster[i] == null || this._disqualified.contains(this._roster[i])) continue;
                currentEnemy = this._roster[i];
                break;
            }
        } else {
            for (Point pair : this._rosterPairs) {
                if (pair.x != playerIndex && pair.y != playerIndex) continue;
                currentEnemy = pair.x != playerIndex ? this._roster[pair.x] : this._roster[pair.y];
                break;
            }
        }
        return currentEnemy;
    }

    public int getPlayerIndex() {
        int index = -1;
        for (int i = 0; i < this._roster.length; ++i) {
            if (this._roster[i] != null) continue;
            index = i;
            break;
        }
        return index;
    }

    private boolean getPlayerBracket(int playerIndex) {
        boolean isLeft = true;
        if (playerIndex > 3) {
            isLeft = false;
        }
        return isLeft;
    }

    private int calcBits() {
        int bits = 0;
        block6: for (Enemy e : this._roster) {
            if (e == null) continue;
            switch (e.getOppStage()) {
                case Rookie: {
                    bits = (int)((double)bits + (double)Config._tourneyRookieBits * this._currentTrophy.getBitModifier());
                    continue block6;
                }
                case Champion: {
                    bits = (int)((double)bits + (double)Config._tourneyChampBits * this._currentTrophy.getBitModifier());
                    continue block6;
                }
                case Ultimate: {
                    bits = (int)((double)bits + (double)Config._tourneyUltBits * this._currentTrophy.getBitModifier());
                    continue block6;
                }
                case Mega: {
                    bits = (int)((double)bits + (double)(this._digimon.getAge() > Config._tourneyRandomMegaAge ? Config._tourneyMaxBits : Config._tourneyMegaBits) * this._currentTrophy.getBitModifier());
                }
            }
        }
        return bits;
    }

    public boolean getNPCWon() {
        return this._disqualified.size() >= 6;
    }
}

