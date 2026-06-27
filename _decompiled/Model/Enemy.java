/*
 * Decompiled with CFR 0.152.
 */
package Model;

import Model.Config;
import Model.ConsumableDrops;
import Model.Enum;
import Model.EvolutionInfo;
import Model.FoodType;
import Model.Item;
import Model.LootTable;
import Model.PhysicalState;
import java.util.ArrayList;

public class Enemy {
    private int _digimonID;
    private int _spriteNum;
    private int _spriteSet;
    private int _map;
    private int _zone;
    private EvolutionInfo _enemy = new EvolutionInfo();
    private int _enemyHealth;
    private int _oppRed;
    private int _oppGreen;
    private int _oppYellow;
    private int _penalty;
    private boolean _isRandom;
    private byte _randomChance;
    private boolean _isZoneBoss;
    private int[] _location = new int[2];
    private Enum.Stage _oppStage;
    private Enum.Attribute _oppAttribute;
    private Enum.Field _oppField;
    private Enum.Element _oppElement;
    private boolean _isSick = false;
    private int[] _bitsWon = new int[]{0, 0};
    private int _cooldown = 0;
    private Enum.AIType _ai = Enum.AIType.Random;
    private ConsumableDrops[] _items;
    private String _bossParadeMessage;
    private Enum.Time _time;

    public void setSpriteNum(int newNum) {
        this._spriteNum = newNum;
    }

    public int getSpriteNum() {
        return this._spriteNum;
    }

    public void setSpriteSet(int newSet) {
        this._spriteSet = newSet;
    }

    public int getSpriteSet() {
        return this._spriteSet;
    }

    public int getIndex() {
        return this._digimonID;
    }

    public void setIndex(int i) {
        this._digimonID = i;
    }

    public boolean getIsZoneBoss() {
        return this._isZoneBoss;
    }

    public void setMap(int newMap) {
        this._map = newMap;
    }

    public int getMap() {
        return this._map;
    }

    public void setZone(int newZone) {
        this._zone = newZone;
    }

    public int getZone() {
        return this._zone;
    }

    public void setEnemyHealth(int newHealth) {
        this._enemyHealth = newHealth;
    }

    public int getEnemyHealth() {
        return this._enemyHealth;
    }

    public void setOppRed(int newRed) {
        this._oppRed = newRed;
    }

    public int getOppRed() {
        return this._oppRed;
    }

    public void setOppGreen(int newGreen) {
        this._oppGreen = newGreen;
    }

    public int getOppGreen() {
        return this._oppGreen;
    }

    public void setOppYellow(int newYellow) {
        this._oppYellow = newYellow;
    }

    public int getOppYellow() {
        return this._oppYellow;
    }

    public void setPenalty(int newPenalty) {
        this._penalty = newPenalty;
    }

    public int getPenalty() {
        return this._penalty;
    }

    public void setIsRandom(boolean newRandom) {
        this._isRandom = newRandom;
    }

    public boolean getIsRandom() {
        return this._isRandom;
    }

    public void setRandomChance(int r) {
        this._randomChance = (byte)r;
    }

    public byte getRandomChance() {
        return this._randomChance;
    }

    public int[] getBitsWon() {
        return this._bitsWon;
    }

    public void setLocation(int[] newLocation) {
        this._location = newLocation;
    }

    public int[] getLocation() {
        return this._location;
    }

    public void setOppStage(Enum.Stage newStage) {
        this._oppStage = newStage;
    }

    public Enum.Stage getOppStage() {
        return this._oppStage;
    }

    public void setOppAttribute(Enum.Attribute newAttribute) {
        this._oppAttribute = newAttribute;
    }

    public Enum.Attribute getOppAttribute() {
        return this._oppAttribute;
    }

    public void setOppField(Enum.Field newField) {
        this._oppField = newField;
    }

    public Enum.Field getOppField() {
        return this._oppField;
    }

    public void setOppElement(Enum.Element e) {
        this._oppElement = e;
    }

    public Enum.Element getOppElement() {
        return this._oppElement;
    }

    public void setIsSick(boolean newSick) {
        this._isSick = newSick;
    }

    public boolean getIsSick() {
        return this._isSick;
    }

    public Enum.AIType getAI() {
        return this._ai;
    }

    public void setAI(Enum.AIType ai) {
        this._ai = ai;
    }

    public ConsumableDrops[] getItems() {
        return this._items;
    }

    public ConsumableDrops[] getAvailableConsumables(PhysicalState digimon) {
        ArrayList<ConsumableDrops> a = new ArrayList<ConsumableDrops>();
        block0: for (ConsumableDrops c : this._items) {
            for (Item i : digimon.getItems()) {
                if (c.isFood() || i.getID() != c.getConsumableID() || !i.canIncQuantity()) continue;
                a.add(c);
                continue block0;
            }
        }
        block2: for (ConsumableDrops c : this._items) {
            for (FoodType f : digimon.getFoodTypes()) {
                if (!c.isFood() || f.getID() != c.getConsumableID() || !f.canIncQuantity()) continue;
                a.add(c);
                continue block2;
            }
        }
        ConsumableDrops[] d = new ConsumableDrops[a.size()];
        return a.toArray(d);
    }

    public int getCooldown() {
        return this._cooldown;
    }

    public void setCooldown(int c) {
        this._cooldown = c;
    }

    public String getBossParadeMessage() {
        return this._bossParadeMessage;
    }

    public Enum.Time getTime() {
        return this._time;
    }

    public Enemy() {
    }

    public Enemy(int spriteNum, int spriteSet, int map, int zone, int enemyHealth, int oppRed, int oppGreen, int oppYellow, int penalty, boolean isRandom, int[] location, Enum.Stage oppStage, Enum.Attribute oppAttribute) {
        this._spriteNum = spriteNum;
        this._spriteSet = spriteSet;
        this._map = map;
        this._zone = zone;
        this._enemyHealth = enemyHealth;
        this._oppRed = oppRed;
        this._oppGreen = oppGreen;
        this._oppYellow = oppYellow;
        this._penalty = penalty;
        this._isRandom = isRandom;
        this._location = location;
        this._oppStage = oppStage;
        this._oppAttribute = oppAttribute;
    }

    private int getMainSpriteNum(int column) {
        return column * 11;
    }

    public void decCooldown() {
        if (this._cooldown > 0) {
            --this._cooldown;
        }
    }

    public void startCooldown() {
        this._cooldown = Config._bossCooldown;
    }

    public boolean isAvailable() {
        return this._cooldown == 0;
    }

    private void setEnemyVariables() {
        this._spriteNum = this._enemy.getNewSpriteNum();
        this._spriteSet = this._enemy.getNewSpriteSet();
        this._oppStage = this._enemy.getNewStage();
        this._oppField = this._enemy.getNewField();
        this._oppElement = this._enemy.getNewElement();
        this._oppAttribute = this._enemy.getNewAttribute();
    }

    public Enemy readInfoString(String enemy, PhysicalState digimon, LootTable loot) {
        String[] info = enemy.split(",");
        this._enemy = digimon.getEvolution().getDigimon(Integer.parseInt(info[1]));
        this._digimonID = Integer.parseInt(info[1]);
        this.setEnemyVariables();
        this._map = Integer.parseInt(info[2]);
        this._zone = Integer.parseInt(info[3]);
        this._enemyHealth = Integer.parseInt(info[4]);
        this._oppRed = Integer.parseInt(info[5]);
        this._oppGreen = Integer.parseInt(info[6]);
        this._oppYellow = Integer.parseInt(info[7]);
        this._penalty = Integer.parseInt(info[8]);
        this._isRandom = Boolean.parseBoolean(info[9]);
        String[] s = info[10].split("t");
        this._location[0] = Integer.parseInt(s[0]);
        this._location[1] = s.length > 1 ? Integer.parseInt(s[1]) : (this._location[0] > 0 ? this._location[0] : Integer.MAX_VALUE);
        this._isZoneBoss = Boolean.parseBoolean(info[11]);
        this._items = loot.getLootTable().get(Integer.valueOf(info[12]));
        try {
            String[] bits = info[13].split("t");
            int b = 0;
            if (bits.length > 1) {
                b = Integer.parseInt(bits[1]);
            }
            this._bitsWon = new int[]{Integer.parseInt(bits[0]), b};
        }
        catch (Exception e) {
            this._bitsWon = new int[]{0};
        }
        this._bossParadeMessage = info[14].equals("null") ? null : info[14];
        this._randomChance = Byte.parseByte(info[15]);
        this._time = Enum.Time.valueOf(info[16]);
        return this;
    }

    public String infoToString() {
        StringBuilder info = new StringBuilder();
        String delin = ",";
        info.append(this._enemy.getName());
        info.append(delin);
        info.append(this._map);
        info.append(delin);
        info.append(this._zone);
        info.append(delin);
        info.append(this._enemyHealth);
        info.append(delin);
        info.append(this._oppRed);
        info.append(delin);
        info.append(this._oppGreen);
        info.append(delin);
        info.append(this._oppYellow);
        info.append(delin);
        info.append(this._penalty);
        info.append(delin);
        info.append(this._isRandom);
        info.append(delin);
        info.append(this._location);
        info.append(delin);
        int loot = -999;
        if (this._items == null) {
            switch (this.getOppAttribute()) {
                case Vaccine: {
                    if (this._enemyHealth >= 20 && (this._oppStage == Enum.Stage.Ultimate || this._oppStage == Enum.Stage.Mega)) {
                        loot = 19;
                        break;
                    }
                    loot = 11;
                    break;
                }
                case Virus: {
                    if (this._enemyHealth >= 20 && (this._oppStage == Enum.Stage.Ultimate || this._oppStage == Enum.Stage.Mega)) {
                        loot = 21;
                        break;
                    }
                    loot = 13;
                    break;
                }
                case Data: {
                    if (this._enemyHealth >= 20 && (this._oppStage == Enum.Stage.Ultimate || this._oppStage == Enum.Stage.Mega)) {
                        loot = 20;
                        break;
                    }
                    loot = 12;
                    break;
                }
                case None: {
                    loot = this._enemyHealth >= 20 && (this._oppStage == Enum.Stage.Ultimate || this._oppStage == Enum.Stage.Mega) ? 22 : 14;
                }
            }
        }
        info.append(loot);
        return info.toString();
    }
}

