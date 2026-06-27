/*
 * Decompiled with CFR 0.152.
 */
package Model;

import Model.Consumable;
import Model.Enum;
import Model.PhysicalState;
import Model.ShopConsumable;
import java.util.ArrayList;

public class Item
extends Consumable {
    private Enum.State _anim;
    private byte _adventureLife;
    private boolean _diminishingReturns;
    private int _itemInterestChange;
    private boolean _useOutside;
    private boolean _useInTown;
    private boolean _isMaxBMGauge;
    private int[] _digimonID;

    public Enum.State getAnim() {
        return this._anim;
    }

    public byte getAdventureLife() {
        return this._adventureLife;
    }

    public int[] getDigimonID() {
        return this._digimonID;
    }

    public boolean getDiminishingReturns() {
        return this._diminishingReturns;
    }

    public int getItemInterestChange() {
        return this._itemInterestChange;
    }

    public boolean useOutside() {
        return this._useOutside;
    }

    public boolean useInTown() {
        return this._useInTown;
    }

    public boolean isMaxBMGauge() {
        return this._isMaxBMGauge;
    }

    public Item(String[] info, int id, int set, int num, Enum.State anim) {
        this(info);
        this._ID = id;
        this._spriteSet = set;
        this._spriteNum = num;
        this._anim = anim;
    }

    public Item(String[] info) {
        String[] unlock;
        this._ID = Integer.parseInt(info[0]);
        this._spriteSet = Integer.parseInt(info[1]);
        this._spriteNum = Integer.parseInt(info[2]);
        this._name = info[3];
        this._description = info[4];
        int price = Integer.parseInt(info[5]);
        this._hunger = Byte.parseByte(info[6]);
        this._strength = Byte.parseByte(info[7]);
        this._energy = Double.parseDouble(info[8]);
        this._obedience = Byte.parseByte(info[9]);
        this._enthusiasm = Byte.parseByte(info[10]);
        this._mood = Integer.parseInt(info[11]);
        this._calories = Byte.parseByte(info[12]);
        this._weight = Byte.parseByte(info[13]);
        this._bmGauge = Byte.parseByte(info[14]);
        this._seconds = Integer.parseInt(info[15]);
        this._vaccine = Byte.parseByte(info[16]);
        this._data = Byte.parseByte(info[17]);
        this._virus = Byte.parseByte(info[18]);
        this._health = Byte.parseByte(info[19]);
        this._recovered = Boolean.parseBoolean(info[20]);
        this._cured = Boolean.parseBoolean(info[21]);
        this._healed = Boolean.parseBoolean(info[22]);
        this._fatigued = Boolean.parseBoolean(info[23]);
        this._depressed = Boolean.parseBoolean(info[24]);
        this._favFood = Enum.Food.valueOf(info[25]);
        this._favTime = Enum.Time.valueOf(info[26]);
        this._newPersonality = Enum.Personality.valueOf(info[27]);
        this._favAttribute = Enum.Attribute.valueOf(info[28]);
        this._mistake = Byte.parseByte(info[29]);
        this._anim = Enum.State.valueOf(info[30]);
        this._sleep = Boolean.parseBoolean(info[31]);
        this._sleepLapse = Integer.parseInt(info[32]);
        this._temp = Byte.parseByte(info[33]);
        this._startingUses = Byte.parseByte(info[34]);
        this._disposition = Byte.parseByte(info[35]);
        this._adventureLife = Byte.parseByte(info[36]);
        this._canIncUses = Boolean.parseBoolean(info[37]);
        this._giftChance = Integer.parseInt(info[38]);
        this._maxUses = Integer.parseInt(info[39]);
        String[] digimon = info[41].split(";");
        this._digimonID = new int[digimon.length];
        for (int i = 0; i < this._digimonID.length; ++i) {
            this._digimonID[i] = Integer.parseInt(digimon[i]);
        }
        this._canUnlock = Boolean.parseBoolean(info[42]);
        this.setShopUnlocked(Boolean.parseBoolean(info[40]));
        this._glutton = Byte.parseByte(info[43]);
        this._restless = Byte.parseByte(info[44]);
        this._dispositionChange = Byte.parseByte(info[45]);
        this._gluttonChange = Byte.parseByte(info[46]);
        this._restlessChange = Byte.parseByte(info[47]);
        this._canDecUses = Boolean.parseBoolean(info[48]);
        this._showInInventory = Boolean.parseBoolean(info[49]);
        String[] s = info[50].split(";");
        byte[] defaultStockChance = new byte[]{Byte.parseByte(s[0]), Byte.parseByte(s[1]), Byte.parseByte(s[2]), Byte.parseByte(s[3])};
        byte defaultMaxStock = Byte.parseByte(info[51]);
        byte defaultMinStock = Byte.parseByte(info[52]);
        String[] ranges = info[53].split(";");
        ArrayList<byte[]> defaultTimeAvailable = new ArrayList<byte[]>();
        for (String r : ranges) {
            String[] time = r.split("t");
            defaultTimeAvailable.add(new byte[]{Byte.parseByte(time[0]), Byte.parseByte(time[1])});
        }
        boolean mustStock = Boolean.parseBoolean(info[54]);
        this._usesPerConsumable = Integer.parseInt(info[55]);
        s = info[56].split(";");
        byte[] saleChance = new byte[]{Byte.parseByte(s[0]), Byte.parseByte(s[1]), Byte.parseByte(s[2]), Byte.parseByte(s[3])};
        byte saleFactor = Byte.parseByte(info[57]);
        byte resellFactor = Byte.parseByte(info[58]);
        this._homeShop = new ShopConsumable(this._ID, false, defaultStockChance, defaultMaxStock, defaultMinStock, defaultTimeAvailable, price, mustStock, saleChance, saleFactor, resellFactor);
        this._healLapseChange = Byte.parseByte(info[59]);
        this._cureLapseChange = Byte.parseByte(info[60]);
        this._fatigueLapseChange = Byte.parseByte(info[61]);
        this._evolProbChange = Integer.parseInt(info[62]);
        this._maxHoursBeforeSleep = Byte.parseByte(info[63]);
        this._effectID = Integer.parseInt(info[64]);
        this._disturb = Boolean.parseBoolean(info[65]);
        this._listPriority = Boolean.parseBoolean(info[66]);
        this._changeToPrefTemp = Boolean.parseBoolean(info[67]);
        this._mistakeDay = Byte.parseByte(info[68]);
        this._forceUse = Boolean.parseBoolean(info[69]);
        this._forceUseWhenAsleep = Boolean.parseBoolean(info[70]);
        for (String u : unlock = info[71].split(";")) {
            this._unlockedFood.add(Integer.valueOf(u));
        }
        if (this._unlockedFood.size() == 1 && (Integer)this._unlockedFood.get(0) == -1) {
            this._unlockedFood.clear();
        }
        for (String u : unlock = info[72].split(";")) {
            this._unlockedItem.add(Integer.valueOf(u));
        }
        if (this._unlockedItem.size() == 1 && (Integer)this._unlockedItem.get(0) == -1) {
            this._unlockedItem.clear();
        }
        this._diminishingReturns = Boolean.parseBoolean(info[73]);
        this._itemInterestChange = Integer.parseInt(info[74]);
        this._isMaxBMGauge = Boolean.parseBoolean(info[75]);
        this._useOutside = Boolean.parseBoolean(info[76]);
        this._useInTown = Boolean.parseBoolean(info[77]);
        this.setCurrentUses(this._startingUses);
        if (!this._canDecUses) {
            this._currentUses = this._maxUses;
        }
    }

    public void unlockItem(PhysicalState digimon) {
        this.unlockConsumable(digimon, Enum.State.UnlockItem);
    }
}

